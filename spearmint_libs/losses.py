

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Time, DateTime, create_engine, ForeignKey
from sqlalchemy.orm import Session, backref, relationship
from sqlalchemy.ext.automap import automap_base


Base = declarative_base()

class ItemsLost(Base):
    __tablename__ = "items_lost"
    id        = Column(Integer, primary_key=True)
    typeID    = Column(Integer)
    parent_id = Column(Integer, ForeignKey('kills.killID'))


class Kills(Base):
    __tablename__ = "kills"
    id         = Column(Integer, primary_key=True)
    shipTypeID = Column(Integer)
    killTime   = Column(DateTime)
    killID     = Column(Integer, unique=True)
    items      = relationship('ItemsLost', backref='kills', lazy='dynamic')


class Losses():
    def __init__(self, config):
        self.base   = automap_base()
        self.engine = create_engine(config['database']['losses'], convert_unicode=True)

        self.base.prepare(self.engine, reflect=True)
        self.session = Session(self.engine)

    def get_query(self):
        return self.session.query
