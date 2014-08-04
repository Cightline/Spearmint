import urllib.request
import urllib.error
import urllib.parse
import xml.etree.cElementTree as ET

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base


class Utils():
    def __init__(self, ccp_db_path):
        self.base = automap_base()
        engine  = create_engine(ccp_db_path, convert_unicode=True)
        self.base.prepare(engine, reflect=True)
        self.session = Session(engine)
        #self.session = ccp_db_session


    def request(self, url, data):
        d = urllib.parse.urlencode(data)
        r = urllib.request.Request(url, 
                                   urllib.parse.urlencode(data).encode('utf-8'))

        return urllib.request.urlopen(r)


    def lookup_typeName(self, id):
        #Base.classes.invTypes is the table, typeName is the column
        q = self.session.query(self.base.classes.invTypes.typeName).filter_by(typeID=id)

        return {'typeName':q.first().typeName} or None

    
    #def search_station(self, query):
        #self.cursor.execute('select stationName,stationId from staStations where stationName like ?', ('%'+query+'%',))
        #return self.cursor.fetchall()

    def search_system(self, name):
        q = self.session.query(self.base.classes.mapSolarSystems).filter(
            self.base.classes.mapSolarSystems.solarSystemName.like(name))
       
        result = q.first()


        if result:
            return {'solarSystemName':result.solarSystemName, 'solarSystemID':result.solarSystemID} 

        return None

    #def search_item(self, query):
    #    self.cursor.execute('select typeName,typeId from invTypes where typeName like ?', ('%'+query+'%',))
    #    return self.cursor.fetchall()



