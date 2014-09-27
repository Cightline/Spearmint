from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Time, DateTime, create_engine, ForeignKey, Boolean
from sqlalchemy.orm import Session, backref, relationship


Base = declarative_base()

class Character(Base):
    __tablename__ = 'characters'
    id           = Column(Integer, primary_key=True)
    character_id = Column(Integer)
    user_id      = Column(Integer, ForeignKey('user.id'))


class Users(Base):
    __tablename__ = 'users'
    id         = Column(Integer, primary_key=True)
    email      = Column(String(120), unique=True)
    password   = Column(String(255))
    api_code   = Column(String(255))
    api_key_id = Column(String(255))
    active     = Column(Boolean)
    activation_code      = Column(String(255))
    recovery_code        = Column(String(255))
    activation_timestamp = Column(DateTime)
    recovery_timestamp   = Column(DateTime)

    characters = relationship('Character', backref='user', lazy='dynamic')

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


