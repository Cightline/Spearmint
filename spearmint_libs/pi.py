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
class StorePi(Base):
    __tablename__ = "pi"
   
    id     = Column(Integer, primary_key=True)
    iteration = Column(Integer)
    system = Column(String(50))
    item   = Column(String(50))
    tier   = Column(Integer)
    price  = Column(Integer)
    date   = Column(String(100))



class Pi():
    def __init__(self, config, utils_obj):
        logging.basicConfig(filename=config['general']['log_path'], level=logging.DEBUG)

        self.store_engine = create_engine(config['database']['pi_db'])
       
        # The key is the "usual" tier, the value is the database value
        self.tiers  = {0:3000, 1:40, 2:5, 3:3}
        self.ec_url = 'http://api.eve-central.com/api/marketstat'
        self.utils  = utils_obj

        self.base = automap_base()
        engine    = create_engine(config['database']['ccp_dump'], convert_unicode=True)
        
        self.base.prepare(engine, reflect=True)
        self.session = Session(engine)

        material_file_path = '%s/constants/planet_materials.json' % (config['general']['install_dir'])
        
        with open(material_file_path) as material_file:
            planet_materials = json.load(material_file)
        

    def get_tiers_id(self, tier):
        '''Returns the typeIDs associated with PI, from the given tier.'''
        ids = []

        q = self.session.query(self.base.classes.planetSchematicsTypeMap).filter_by(quantity=self.tiers[tier])

        for row in q.all():
            to_append = row.typeID
            # Prevent duplicates
            if to_append not in ids:
                ids.append(to_append)
        
        if len(ids):
            return ids

        return False

    def get_prices(self, tier, system):
        Session = sessionmaker(bind=self.store_engine)
        store_session = Session()

        query =  store_session.query(StorePi).filter_by(system=system, tier=tier).order_by(StorePi.iteration.desc()).first() or None

        if query:
            iteration = query.iteration
            return store_session.query(StorePi).filter_by(iteration=query.iteration, system=system, tier=tier).order_by(StorePi.price.desc()).all()

        return False


    def store_prices(self, tier, system):
        '''This obviously stores prices in the database. Everytime it runs, it increments the "iteration" \
           integer from the database so I can keep things organized a little bit better.'''

        ids    = self.get_tiers_id(tier)
        prices = {}
        count  = 0
        
        Session = sessionmaker(bind=self.store_engine)
        store_session = Session()

        # Why the fuck do I have to add this?
        store_session._model_changes = {}
 
        # Lookup the last iteration int stored, and add one. If it does not exist, start at 1
        query = store_session.query(StorePi).order_by(StorePi.iteration.desc()).first() or None

        if query:
            iteration = query.iteration + 1

        else:
            iteration = 1

        # Store the time this iteration was cached
        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for id_ in ids:
            count += 1
            logging.info('storing PI information from system: %s, tier: %s -- %s of %s' % (system, tier, count, len(ids)))

            item = self.utils.lookup_typeName(id_)['typeName']
            data = {'typeid':id_, 'usesystem':system}
            page = requests.get(self.ec_url, params=data)

            if page.status_code != 200:
                logging.warning('page.status_code is %s, expecting 200' % (page.status_code))
                return False


            root = ET.fromstring(page.text)
            
            for b in root.iter('buy'):
                maximum = b.find('max').text
                
                to_store = StorePi(tier=tier, 
                                   price=maximum, 
                                   system=system,
                                   item=item,
                                   date=date,
                                   iteration=iteration) 

                store_session.add(to_store)
                store_session.commit()
                
                prices[float(maximum)] = self.utils.lookup_typeName(id_)['typeName']
                break
        
