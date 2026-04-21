import threading
import uuid
import tempfile
import shutil
import subprocess
import time as _time
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_user, logout_user, login_required

from .extensions import db, login_manager
from .models import User, Species, SpeciesClassSummary, OrderSummary, KeySpecies, AtRiskSpecies, TimeDotObservation, SurveyObservation

bp = Blueprint('main', __name__)

# In-memory job store: {job_id: {status, total, fetched, batches, batch, error, output_path}}
_jobs: dict = {}
_JOB_TTL = 3600  # seconds to keep finished jobs


def _cleanup_jobs():
    now = _time.time()
    stale = [jid for jid, j in _jobs.items()
             if j.get('status') in ('done', 'error') and now - j.get('finished_at', now) > _JOB_TTL]
    for jid in stale:
        _jobs.pop(jid, None)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@bp.route('/download-ala', methods=['GET'])
@login_required
def download_ala_page():
    return render_template('download_ala.html')


@bp.route('/download-ala/start', methods=['POST'])
@login_required
def download_ala_start():
    _cleanup_jobs()
    from .download_ala import download_ala_from_kml
    kml_file = request.files.get('kml_file')
    if not kml_file or not kml_file.filename.endswith('.kml'):
        return jsonify({'error': 'Please upload a valid .kml file.'}), 400

    job_id = str(uuid.uuid4())
    tmp_dir = Path(tempfile.mkdtemp())
    kml_path = tmp_dir / 'input.kml'
    output_path = tmp_dir / 'Glenbog.csv'
    kml_file.save(str(kml_path))

    # Persist KML so maps can draw the boundary
    boundary_dest = Path(__file__).parent / 'static' / 'boundary.kml'
    shutil.copy2(str(kml_path), str(boundary_dest))

    CLEAN_SCRIPTS = [
        '/data/Species_Summary.py',
        '/data/Class_Summary.py',
        '/data/Order_Summary.py',
        '/data/At_Risk_Species.py',
        '/data/Key_Species.py',
        '/data/SurveyMap_Past6Months.py',
        '/data/TimeDotGraph_Data.py',
    ]
    IMPORT_SCRIPTS = [
        '/app/scripts/import_species.py',
        '/app/scripts/import_class_summary.py',
        '/app/scripts/import_order_summary.py',
        '/app/scripts/import_at_risk_species.py',
        '/app/scripts/import_key_species.py',
        '/app/scripts/import_survey_map.py',
        '/app/scripts/import_time_dot.py',
    ]
    all_scripts = [('clean', s) for s in CLEAN_SCRIPTS] + [('import', s) for s in IMPORT_SCRIPTS]
    steps = [{'name': Path(s).stem, 'type': t, 'status': 'pending'} for t, s in all_scripts]

    progress = {
        'status': 'downloading',
        'total': 0, 'fetched': 0, 'batches': 0, 'batch': 0,
        'steps': steps,
        'output_path': str(output_path),
    }
    _jobs[job_id] = progress

    def run():
        try:
            # Step 1: download from ALA
            download_ala_from_kml(kml_path, output_path, progress)

            # Step 2: copy to /data/Glenbog.csv
            progress['status'] = 'copying'
            shutil.copy2(str(output_path), '/data/Glenbog.csv')

            # Step 3: run cleaning + import scripts
            for i, (_, script) in enumerate(all_scripts):
                steps[i]['status'] = 'running'
                result = subprocess.run(
                    ['python', script],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    steps[i]['status'] = 'error'
                    steps[i]['error'] = result.stderr[-300:] if result.stderr else 'Unknown error'
                    progress['status'] = 'error'
                    progress['error'] = f"{Path(script).stem} failed"
                    progress['finished_at'] = _time.time()
                    return
                steps[i]['status'] = 'done'

            progress['status'] = 'done'
            progress['finished_at'] = _time.time()
        except Exception as e:
            progress['status'] = 'error'
            progress['error'] = str(e)
            progress['finished_at'] = _time.time()

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'job_id': job_id})


@bp.route('/download-ala/status/<job_id>')
@login_required
def download_ala_status(job_id):
    job = _jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({k: v for k, v in job.items() if k != 'output_path'})


@bp.route('/download-ala/result/<job_id>')
@login_required
def download_ala_result(job_id):
    job = _jobs.get(job_id)
    if not job or job.get('status') != 'done':
        return 'Not ready', 404
    return send_file(job['output_path'], as_attachment=True, download_name='Glenbog.csv')



@bp.route('/')
@login_required
def index():
    return render_template('index.html')


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if not email or not password or not password2:
            flash('Please fill in all fields.')
            return redirect(url_for('main.register'))
        if password != password2:
            flash('Passwords do not match.')
            return redirect(url_for('main.register'))
        if User.query.filter_by(email=email).first():
            flash('This email is already registered.')
            return redirect(url_for('main.register'))

        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('main.login'))

    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.')
            return redirect(url_for('main.index'))

        flash('Incorrect email or password.')
        return redirect(url_for('main.login'))

    return render_template('login.html')


@bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@bp.route('/survey-map/data')
@login_required
def survey_map_data():
    from flask import jsonify
    date_str = request.args.get('date', '')
    resource = request.args.get('resource', '')
    obs = SurveyObservation.query.filter_by(
        data_resource_name=resource
    ).filter(
        SurveyObservation.event_date == date_str
    ).all()
    return jsonify([{
        'lat': o.latitude,
        'lng': o.longitude,
        'scientific': o.scientific_name,
        'common': o.vernacular_name,
        'recorded_by': o.recorded_by,
    } for o in obs])


@bp.route('/survey-map')
@login_required
def survey_map():
    from collections import defaultdict
    observations = SurveyObservation.query.order_by(
        SurveyObservation.event_date, SurveyObservation.data_resource_name
    ).all()

    # Group by (event_date, data_resource_name)
    surveys = defaultdict(list)
    for obs in observations:
        key = (obs.event_date.strftime('%Y-%m-%d'), obs.data_resource_name)
        surveys[key].append(obs)

    survey_keys = list(surveys.keys())
    selected_raw = request.args.get('survey', '')
    # Parse "date|resource" back to tuple
    if '|' in selected_raw:
        parts = selected_raw.split('|', 1)
        selected_key = (parts[0], parts[1])
    else:
        selected_key = None
    if not selected_key or selected_key not in surveys:
        selected_key = survey_keys[0] if survey_keys else None

    selected_obs = surveys.get(selected_key, [])
    return render_template('survey_map.html', survey_keys=survey_keys, selected_key=selected_key, observations=selected_obs)


@bp.route('/time-dot-graph')
@login_required
def time_dot_graph():
    observations = TimeDotObservation.query.order_by(TimeDotObservation.scientific_name, TimeDotObservation.event_date).all()
    return render_template('time_dot_graph.html', observations=observations)


def _load_glenbog_boundary():
    import re
    # Prefer the user-uploaded boundary, fall back to the default one
    candidates = [
        Path(__file__).parent / 'static' / 'boundary.kml',
        Path('/data/Glenbog Boundary.kml'),
    ]
    for kml_path in candidates:
        try:
            text = kml_path.read_text(encoding='utf-8')
            coords = []
            for match in re.finditer(r'<coordinates>(.*?)</coordinates>', text, re.DOTALL):
                for token in match.group(1).split():
                    parts = token.split(',')
                    if len(parts) >= 2:
                        coords.append([float(parts[1]), float(parts[0])])
            if coords:
                return coords
        except Exception:
            continue
    return []


@bp.route('/api/boundary')
@login_required
def api_boundary():
    return jsonify(_load_glenbog_boundary())


@bp.route('/map')
@login_required
def species_map():
    species = AtRiskSpecies.query.filter(
        AtRiskSpecies.latitude.isnot(None),
        AtRiskSpecies.longitude.isnot(None)
    ).all()
    return render_template('map.html', species=species)


@bp.route('/species/at-risk')
@login_required
def at_risk_species():
    page = request.args.get('page', 1, type=int)
    pagination = AtRiskSpecies.query.order_by(AtRiskSpecies.scientific_name).paginate(page=page, per_page=6, error_out=False)
    return render_template('at_risk_species.html', species=pagination.items, pagination=pagination)


@bp.route('/species/key')
@login_required
def key_species():
    page = request.args.get('page', 1, type=int)
    pagination = KeySpecies.query.order_by(KeySpecies.class_display, KeySpecies.common_name).paginate(page=page, per_page=6, error_out=False)
    return render_template('key_species.html', species=pagination.items, pagination=pagination)


@bp.route('/order-summary')
@login_required
def order_summary():
    all_summaries = OrderSummary.query.order_by(OrderSummary.total_observations.desc()).all()
    total_obs = sum(s.total_observations for s in all_summaries)
    total_species = sum(s.total_species for s in all_summaries)
    page = request.args.get('page', 1, type=int)
    pagination = OrderSummary.query.order_by(OrderSummary.total_observations.desc()).paginate(page=page, per_page=6, error_out=False)
    return render_template('order_summary.html', summaries=pagination.items, pagination=pagination, total_obs=total_obs, total_species=total_species)


@bp.route('/species/stats')
@login_required
def species_stats():
    summaries = SpeciesClassSummary.query.order_by(SpeciesClassSummary.num_observations.desc()).all()
    total_obs = sum(s.num_observations for s in summaries)
    total_species = sum(s.num_species for s in summaries)
    return render_template('species_stats.html', summaries=summaries, total_obs=total_obs, total_species=total_species)


@bp.route('/species')
@login_required
def species_list():
    page = request.args.get('page', 1, type=int)
    pagination = Species.query.order_by(Species.class_display, Species.vernacular_name).paginate(page=page, per_page=6, error_out=False)
    return render_template('species.html', species=pagination.items, pagination=pagination)
