from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required

from .extensions import db, login_manager
from .models import User, Species, SpeciesClassSummary, KeySpecies, AtRiskSpecies, TimeDotObservation, SurveyObservation

bp = Blueprint('main', __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


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
