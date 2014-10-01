from spearmint_libs.sql import *

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
    characterID   = Column(Integer)
    allianceID    = Column(Integer)
    corporationID = Column(Integer)
    items       = relationship('ItemsLost', backref='kills', lazy='dynamic')

    
