from spearmint_libs.sql import *

# Class to store the info from eve-central
class Pi(Base):
    __tablename__ = "pi"
   
    id     = Column(Integer, primary_key=True)
    iteration = Column(Integer)
    system = Column(String(50))
    item   = Column(String(50))
    tier   = Column(Integer)
    price  = Column(Integer)
    date   = Column(String(100))

