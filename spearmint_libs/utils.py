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


    def lookup_typename(self, id):
        #Base.classes.invTypes is the table, typeName is the column
        q = self.session.query(self.base.classes.invTypes.typeName).filter_by(typeID=id)

        result = q.first()

        if result:
            return result[0]
    
        return None
        
    def lookup_system(self, name):
        query = self.session.query(self.base.classes.mapSolarSystems).filter(
            self.base.classes.mapSolarSystems.solarSystemName.like(name))
       
        return query.first() or None


    def lookup_planets(self, solarSystemID):
        #sqlite> select * from mapDenormalize where itemID = 40000002;
        #itemID      typeID      groupID     solarSystemID  constellationID  regionID    orbitID     x               y              z               radius      itemName    security    celestialIndex  orbitIndex
        #----------  ----------  ----------  -------------  ---------------  ----------  ----------  --------------  -------------  --------------  ----------  ----------  ----------  --------------  ----------
        #40000002    11          7           30000001       20000001         10000001    40000001    161891117336.0  21288951986.0  -73529712226.0  5060000.0   Tanoo I     0.858324    1                         
        #sqlite> 
        
        data = self.session.query(self.base.classes.mapDenormalize).filter_by(groupID=7, solarSystemID=solarSystemID)

        return data
