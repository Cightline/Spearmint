import xml.etree.cElementTree as ET
import os
import datetime
import logging  
import json

from sqlalchemy import create_engine,  Table, Column, Integer, String, Time
from sqlalchemy.orm import mapper, Session, load_only, sessionmaker
from sqlalchemy.ext.automap import automap_base

import requests

from spearmint_libs.utils import Utils
from spearmint_libs.sql.db_connect import Connect



class PiUtils():
    def __init__(self, config, utils_obj):
        logging.basicConfig(filename='%s/log' % (config['general']['base_dir']), level=logging.DEBUG)

        self.db = Connect(config['database']['data'])
        self.classes = self.db.base.classes
       
        # The key is the "usual" tier, the value is the database value
        self.tiers  = {0:3000, 1:40, 2:5, 3:3}
        self.ec_url = 'http://api.eve-central.com/api/marketstat'
        self.utils  = utils_obj

        self.ccp_db = Connect(config['database']['ccp_dump'])
        

        material_file_path = '%s/constants/planet_materials.json' % (config['general']['base_dir'])
        
        with open(material_file_path) as material_file:
            planet_materials = json.load(material_file)
        

    def get_tiers_id(self, tier):
        '''Returns the typeIDs associated with PI, from the given tier.'''
        ids = []

        q = self.ccp_db.session.query(self.ccp_db.base.classes.planetSchematicsTypeMap).filter_by(quantity=self.tiers[tier])

        for row in q.all():
            to_append = row.typeID
            # Prevent duplicates
            if to_append not in ids:
                ids.append(to_append)
        
        if len(ids):
            return ids

        return False

    def get_prices(self, tier, system):

        '''Returns a sqlalchemy "Pi" object with the prices from the database'''

        query = self.db.session.query(self.classes.pi).filter_by(system=system, tier=tier).all()

        return query or None


    def store_prices(self, tier, system):
        '''This obviously stores prices in the database. Everytime it runs, it increments the "iteration" \
           integer from the database so I can keep things organized a little bit better.'''

        ids    = self.get_tiers_id(tier)
        prices = {}
        count  = 0
        
 
        # Store the time this iteration was cached
        date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for id_ in ids:
            count += 1
            logging.info('storing PI information from system: %s, tier: %s -- %s of %s' % (system, tier, count, len(ids)))

            item = self.utils.lookup_typename(id_)
            data = {'typeid':id_, 'usesystem':system}
            page = requests.get(self.ec_url, params=data)

            if page.status_code != 200:
                logging.warning('page.status_code is %s, expecting 200' % (page.status_code))
                return False

            root = ET.fromstring(page.text)
            
            for b in root.iter('buy'):
                maximum = b.find('max').text
                
                to_store = self.classes.pi(
                        tier=tier, 
                        price=maximum, 
                        system=system,
                        item=item,
                        date=date) 

                self.db.session.add(to_store)
                self.db.session.commit()
                
                break
        
