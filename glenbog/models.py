from flask_login import UserMixin

from .extensions import db, bcrypt


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class Species(db.Model):
    __tablename__ = 'species'
    id = db.Column(db.Integer, primary_key=True)
    class_display = db.Column(db.String(100), nullable=False)
    order = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(255), nullable=False)
    vernacular_name = db.Column(db.String(255), nullable=False)
    num_observations = db.Column(db.Integer, default=0)
    most_recent_date = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<Species {self.vernacular_name}>'


class SpeciesClassSummary(db.Model):
    __tablename__ = 'class_summary'
    id = db.Column(db.Integer, primary_key=True)
    class_display = db.Column(db.String(100), nullable=False)
    num_observations = db.Column(db.Integer, default=0)
    num_species = db.Column(db.Integer, default=0)
    class_description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<SpeciesClassSummary {self.class_display}>'


class KeySpecies(db.Model):
    __tablename__ = 'key_species'
    id = db.Column(db.Integer, primary_key=True)
    class_display = db.Column(db.String(100), nullable=False)
    common_name = db.Column(db.String(255), nullable=False)
    scientific_name = db.Column(db.String(255), nullable=False)
    num_observations = db.Column(db.Integer, default=0)
    most_recent_date = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f'<KeySpecies {self.common_name}>'


class AtRiskSpecies(db.Model):
    __tablename__ = 'at_risk_species'
    id = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(255), nullable=False)
    common_name = db.Column(db.String(255), nullable=False)
    class_display = db.Column(db.String(100))
    order = db.Column(db.String(100))
    num_observations = db.Column(db.Integer, default=0)
    date_of_observation = db.Column(db.Date, nullable=True)
    status = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f'<AtRiskSpecies {self.common_name}>'


class OrderSummary(db.Model):
    __tablename__ = 'order_summary'
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.String(100), nullable=False)
    class_display = db.Column(db.String(100), nullable=False)
    total_species = db.Column(db.Integer, default=0)
    total_observations = db.Column(db.Integer, default=0)
    proportion = db.Column(db.Float, default=0.0)
    order_description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<OrderSummary {self.order}>'


class TimeDotObservation(db.Model):
    __tablename__ = 'time_dot_observations'
    id = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(255), nullable=False)
    vernacular_name = db.Column(db.String(255), nullable=False)
    class_display = db.Column(db.String(100))
    order = db.Column(db.String(100))
    family = db.Column(db.String(100))
    event_date = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f'<TimeDotObservation {self.scientific_name} {self.event_date}>'


class SurveyObservation(db.Model):
    __tablename__ = 'survey_observations'
    id = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(255), nullable=False)
    vernacular_name = db.Column(db.String(255), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    data_resource_name = db.Column(db.String(255))
    recorded_by = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<SurveyObservation {self.scientific_name} {self.event_date}>'


class BirdTrait(db.Model):
    __tablename__ = 'bird_traits'
    id = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(255), nullable=False)
    common_name = db.Column(db.String(255), nullable=False)
    most_recent_date = db.Column(db.Date, nullable=True)
    iucn_status = db.Column(db.String(10), nullable=True)
    primary_habitat = db.Column(db.String(100), nullable=True)
    primary_diet = db.Column(db.String(100), nullable=True)
    average_mass_g = db.Column(db.Float, nullable=True)
    migratory = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<BirdTrait {self.common_name}>'
