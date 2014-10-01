from spearmint_libs.sql import *

class ItemsLost(Base):
    __tablename__ = "items_lost"
    id        = Column(Integer, primary_key=True)
    typeID    = Column(Integer)
    killID    = Column(Integer, ForeignKey('kills.killID'))

class Attacker(Base):
    __tablename__ = 'attacker'
    id              = Column(Integer, primary_key=True)
    killID          = Column(Integer, ForeignKey('kills.killID'))
    weaponTypeID    = Column(Integer)
    allianceID      = Column(Integer)
    corporationName = Column(String(255))
    shipTypeID      = Column(Integer)
    characterName   = Column(String(255))
    characterID     = Column(Integer)
    allianceName    = Column(String(255))
    killTime        = Column(DateTime, ForeignKey('kills.killTime'))

class Kills(Base):
    __tablename__ = "kills"
    id         = Column(Integer, primary_key=True)
    shipTypeID = Column(Integer)
    killTime   = Column(DateTime)
    killID     = Column(Integer, unique=True)
    characterID   = Column(Integer)
    allianceID    = Column(Integer)
    corporationID = Column(Integer)
    corporationName = Column(String(255))
    items       = relationship('ItemsLost', backref='kills', lazy='dynamic')
    attackers   = relationship('Attacker',  backref='kills', lazy='dynamic')

    
