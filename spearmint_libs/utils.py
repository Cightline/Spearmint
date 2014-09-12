import xml.etree.cElementTree as ET
import datetime
import hashlib
import os

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base


def generate_code():
    return hashlib.sha1(os.urandom(1488)).hexdigest()


def format_time(timestamp):
    if timestamp:
        return datetime.datetime.utcfromtimestamp(timestamp).isoformat()
    else:
        return 'N/A'


def format_currency(amount):
    return '{:,.2f}'.format(amount)


class Utils():
    def __init__(self, config):
        self.base = automap_base()
        engine  = create_engine(config['database']['ccp_dump'], convert_unicode=True)
        self.base.prepare(engine, reflect=True)
        self.session = Session(engine)


    def lookup_typeName(self, id):
        #Base.classes.invTypes is the table, typeName is the column
        q = self.session.query(self.base.classes.invTypes.typeName).filter_by(typeID=id)

        return {'typeName':q.first().typeName} or None

    
    def search_system(self, name):
        q = self.session.query(self.base.classes.mapSolarSystems).filter(
            self.base.classes.mapSolarSystems.solarSystemName.like(name))
       
        result = q.first()


        if result:
            return {'solarSystemName':result.solarSystemName, 'solarSystemID':result.solarSystemID} 

        return None



