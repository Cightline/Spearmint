import sqlite3
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.cElementTree as ET

class Utils():
    def __init__(self):
        self.conn   = sqlite3.connect('sqlite-latest.sqlite')
        self.cursor = self.conn.cursor()


    def request(self, url, data):
        d = urllib.parse.urlencode(data)
        r = urllib.request.Request(url, 
                                   urllib.parse.urlencode(data).encode('utf-8'))

        return urllib.request.urlopen(r)


    def id_to_name(self, id_, multiple=False):
        self.cursor.execute('select typeName from invTypes where typeId = ?', (id_))
        if multiple:
            return self.cursor.fetchall()

        return self.cursor.fetchone()

    
    def search_station(self, query):
        self.cursor.execute('select stationName,stationId from staStations where stationName like ?', ('%'+query+'%',))
        return self.cursor.fetchall()

    def search_system(self, query):
        self.cursor.execute('select solarSystemName,solarSystemID from mapSolarSystems where solarSystemName like ?', ('%'+query+'%',))
        return self.cursor.fetchall()

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

