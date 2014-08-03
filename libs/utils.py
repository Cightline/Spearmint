import urllib.request
import urllib.error
import urllib.parse
import xml.etree.cElementTree as ET

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base

Base = automap_base()
db_path = 'sqlite:////%s/sqlite-latest.sqlite' % ('home/stealth/programming/spearmint')
engine  = create_engine(db_path, convert_unicode=True)

Base.prepare(engine, reflect=True)

session = Session(engine)

class Utils():
    def __init__(self):
        pass

    def request(self, url, data):
        d = urllib.parse.urlencode(data)
        r = urllib.request.Request(url, 
                                   urllib.parse.urlencode(data).encode('utf-8'))

        return urllib.request.urlopen(r)


    def lookup_typeName(self, id):
        #Base.classes.invTypes is the table, typeName is the column
        q = session.query(Base.classes.invTypes.typeName).filter_by(typeID=id)

        return {'typeName':q.first().typeName} or None

    
    def search_station(self, query):
        self.cursor.execute('select stationName,stationId from staStations where stationName like ?', ('%'+query+'%',))
        return self.cursor.fetchall()

    def search_system(self, name):
        q = session.query(Base.classes.mapSolarSystems).filter(
            Base.classes.mapSolarSystems.solarSystemName.like(name))
       
        result = q.first()


        if result:
            return {'solarSystemName':result.solarSystemName, 'solarSystemID':result.solarSystemID} 

        return None

    def search_item(self, query):
        self.cursor.execute('select typeName,typeId from invTypes where typeName like ?', ('%'+query+'%',))
        return self.cursor.fetchall()



if __name__ == "__main__":
    u = Utils()

    for row in u.search_station('Jita'):
        print(row)

    for row in u.search_item('Slave'):
        print(row)

    for row in u.search_system('jita'):
        print(row)

