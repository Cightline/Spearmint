import xml.etree.cElementTree as ET

from sqlalchemy import create_engine,  Table
from sqlalchemy.orm import mapper, Session, load_only
from sqlalchemy.ext.automap import automap_base

from libs import utils







class Pi():
    def __init__(self):
        # First int is the usual tier people use, the 2nd int is the database version
        self.tiers  = {0:3000, 1:40, 2:5, 3:3}
        self.ec_url = 'http://api.eve-central.com/api/marketstat'
        self.utils = utils.Utils()

        db_path = 'sqlite:////%s/sqlite-latest.sqlite' % ('home/stealth/programming/spearmint')
        Base = automap_base()
        engine = create_engine(db_path, convert_unicode=True)
        Base.prepare(engine, reflect=True)
        self.session = Session(engine)
                
    def get_tiers_id(self, tier):
        ids = []

        q = self.session.query(Base.classes.planetSchematicsTypeMap).filter_by(quantity=self.tiers[tier])

        for row in q.all():
            ids.append(row.typeID)


        return ids 
         

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
                prices[float(maximum)] = self.utils.lookup_typeName(i)['typeName']
                break
                
        return prices

    

if __name__ == "__main__":
    p = Pi()
    items = p.lookup_prices(2)

    items_sorted = list(items.keys())
    items_sorted.sort()

    for item in items_sorted:
        print(items[item], item)

