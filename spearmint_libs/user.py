from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Character(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True)
    password   = db.Column(db.String(255))
    api_code   = db.Column(db.String(255))
    api_key_id = db.Column(db.String(255))
    active     = db.Column(db.Boolean)
    activation_code      = db.Column(db.String(255))
    recovery_code        = db.Column(db.String(255))
    activation_timestamp = db.Column(db.DateTime())
    recovery_timestamp   = db.Column(db.DateTime())

    characters = db.relationship('Character', backref='user', lazy='dynamic')

    def is_active(self):
        # Change this
        return True


    def is_authenticated(self):
        # and this
        return True
    
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.email

    def __unicode__(self):
        return self.email


