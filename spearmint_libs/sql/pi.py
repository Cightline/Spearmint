import xml.etree.cElementTree as ET
import os
import datetime
import logging  
import json

from sqlalchemy import create_engine,  Table, Column, Integer, String, Time
from sqlalchemy.orm import mapper, Session, load_only, sessionmaker
from sqlalchemy.ext.automap import automap_base

import requests

from spearmint_libs import utils

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


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

