import xml.etree.cElementTree as ET
import os
import datetime

from sqlalchemy import create_engine,  Table, Column, Integer, String, Date
from sqlalchemy.orm import mapper, Session, load_only, sessionmaker
from sqlalchemy.ext.automap import automap_base

from spearmint_libs import utils

from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

# Class to store the info from eve-central
class StorePi(Base):
    __tablename__ = "pi"
   
    id     = Column(Integer, primary_key=True)
    iteration = Column(Integer)
    system = Column(String(50))
    item   = Column(String(50))
    tier   = Column(Integer)
    price  = Column(Integer)
    date   = Column(Date)






class Pi():
    def __init__(self, ccp_db_path, pi_db_path, utils_obj):
        self.store_engine = create_engine(pi_db_path)
        # First int is the usual tier people use, the 2nd int is the database version
        self.tiers  = {0:3000, 1:40, 2:5, 3:3}
        self.ec_url = 'http://api.eve-central.com/api/marketstat'
        self.utils = utils_obj

        self.base = automap_base()
        engine = create_engine(ccp_db_path, convert_unicode=True)
        self.base.prepare(engine, reflect=True)
        self.session = Session(engine)

                
    def get_tiers_id(self, tier):
        # Returns the typeIDs associated with PI, from the given tier.
        ids = []

        q = self.session.query(self.base.classes.planetSchematicsTypeMap).filter_by(quantity=self.tiers[tier])

        for row in q.all():
            to_append = row.typeID
            # Prevent duplicates
            if to_append not in ids:
                ids.append(to_append)
        
        return ids 

    def get_prices(self, tier, system):
        Session = sessionmaker(bind=self.store_engine)
        store_session = Session()

        query =  store_session.query(StorePi).filter_by(system=system, tier=tier).order_by(StorePi.iteration.desc()).first() or None

        if query:
            iteration = query.iteration
            return store_session.query(StorePi).filter_by(iteration=query.iteration, system=system, tier=tier).order_by(StorePi.price.desc()).all()

        return False


    def store_prices(self, tier, system):
        ids    = self.get_tiers_id(tier)
        prices = {}
        
        Session = sessionmaker(bind=self.store_engine)

        store_session = Session()

        # Why the fuck do I have to add this?
        store_session._model_changes = {}
        
        query = store_session.query(StorePi).order_by(StorePi.iteration.desc()).first() or None


        if not query:
            iteration = 1

            
        else:
            iteration = query.iteration + 1 
      
            print('iteration: ', iteration)

        for i in ids:
            item = self.utils.lookup_typeName(i)['typeName']
            data = {'typeid':i, 'usesystem':system}
            page = self.utils.request(self.ec_url, data)

            tree = ET.parse(page)
            root = tree.getroot()
            
            time = datetime.datetime.now()
            

            for b in root.iter('buy'):
                maximum = b.find('max').text
                
                to_store = StorePi(tier=tier, 
                                   price=maximum, 
                                   system=system,
                                   item=item,
                                   date=time,
                                   iteration=iteration) 

                print(item)
                store_session.add(to_store)
                store_session.commit()
                
                prices[float(maximum)] = self.utils.lookup_typeName(i)['typeName']
                break
        
          

