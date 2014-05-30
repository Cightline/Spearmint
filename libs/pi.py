import sqlite3
import urllib.request, urllib.error, urllib.parse
import urllib.request, urllib.parse, urllib.error
import xml.etree.cElementTree as ET

from libs import utils

class Pi():
    def __init__(self):
        self.conn   = sqlite3.connect('sqlite-latest.sqlite')
        self.cursor = self.conn.cursor()
        self.tiers  = {0:3000, 1:40, 2:5, 3:3}
        self.ec_url = 'http://api.eve-central.com/api/marketstat'
        self.utils = utils.Utils()

                
    def get_tiers_id(self, tier):
        ids = []
        self.cursor.execute('select * from planetSchematicsTypeMap where quantity = ?', (self.tiers[tier],))
        for row in self.cursor.fetchall():
            ids.append(row[1])

        return ids
         
    def lookup_name(self, id_, multiple=False):
        self.cursor.execute('select typeName from invTypes where typeID = ?', (id_,))

        if multiple:
            return self.cursor.fetchall()

        return self.cursor.fetchone()


    def lookup_prices(self, tier, region=None, system=30000142):
        ids    = self.get_tiers_id(tier)
        prices = {}

        for i in ids:
            data = {'typeid':i, 'usesystem':system}
            page = self.utils.request(self.ec_url, data)

            tree = ET.parse(page)
            
            root = tree.getroot()

            for b in root.iter('buy'):
                maximum = b.find('max').text
                prices[float(maximum)] = self.lookup_name(i)
                break
                
        return prices

    

if __name__ == "__main__":
    p = PI()
    items = p.lookup_prices(2)

    items_sorted = list(items.keys())
    items_sorted.sort()

    for item in items_sorted:
        print(items[item], item)

