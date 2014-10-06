import argparse
import json 
import datetime

import requests

from sqlalchemy import *
from sqlalchemy.orm import Session, sessionmaker

from spearmint_libs.pi_utils     import PiUtils
from spearmint_libs.utils  import Utils, format_time
from spearmint_libs.sql.db_connect import Connect

import evelink



class Command():
    def __init__(self):
        self.config = self.read_config()
        self.utils  = Utils(self.config)
        self.pi_utils = PiUtils(self.config, self.utils)
        self.eve    = evelink.eve.EVE()
        self.corp_api = evelink.api.API(api_key=(self.config['corp_api']['key'], self.config['corp_api']['code']))
        self.corp     = evelink.corp.Corp(self.corp_api)
        self.db       = Connect(self.config['database']['data'])


        parser = argparse.ArgumentParser()
        parser.add_argument('--pi',        help='update the PI cache',  action='store_true')
        parser.add_argument('--losses',    help='update the items and ships that have been destroyed', action='store', type=int)
        parser.add_argument('--coalition', help='coalition or alliance for --losses', action='store', type=str)
        parser.add_argument('--create-db', help='create the databases', action='store_true')
        parser.add_argument('--start',     help='page to start at for updating losses', action='store', type=int)
        self.args = parser.parse_args()

        if self.args.pi:
            self.update_pi()

        if self.args.losses:
            self.update_losses()

        if self.args.create_db:
            self.create_databases()

    def read_config(self, path='config.json'):
        with open(path) as cfg:
            config = json.loads(cfg.read())
            assert(config)

            return config

    def display_completion(self, percentage):
        print(int(percentage))

    def update_losses(self):
        print('Updating losses...')

        losses      = self.db
        items_lost_  = {}
        alliance_ids = []
        alliances_requested = []

        for coalition in self.config['coalitions']:
            alliance_ids.extend(self.config['coalitions'][coalition])

        if self.args.start:
            start_page = self.args.start

        else:
            start_page = 0

        for count in range(start_page, self.args.losses):
            print('Page %s of %s' % (count, self.args.losses))

            for alliance_id in alliance_ids:

                if alliance_id in alliances_requested:
                    continue

                alliances_requested.append(alliance_id)
                print('Alliance %s' % (alliance_id))
                kb_url =  'https://zkillboard.com/api/kills/allianceID/%s/page/%s/' % (alliance_id, count)
                
                data = json.loads(requests.get(kb_url).text)

                for row in data:
                    
                    # I'm putting row_count up here because its possible to already have the kill in the db. 

                    #self.display_completion(row_count)
                    # 'killTime': '2014-09-19 21:27:00'
                    time_format = '%Y-%m-%d %H:%M:%S'
                    kill_time = datetime.datetime.strptime(row['killTime'], time_format)
                    kill_id   = row['killID']
                
                    query = losses.session.query(losses.base.classes.kills).filter_by(killID=kill_id).first()

                    if query:
                        #print('killID already exists, skipping')
                        continue
   
        
                    kill = losses.base.classes.kills(killID=kill_id, 
                             shipTypeID=row['victim']['shipTypeID'], 
                             killTime=kill_time,
                             characterID=row['victim']['characterID'],
                             corporationID=row['victim']['corporationID'],
                             corporationName=row['victim']['corporationName'],
                             allianceID=row['victim']['allianceID'])


                    for line in row['items']:
                        #print('storing item: %s' % (self.utils.lookup_typename(line['typeID'])))
                        item = losses.base.classes.items_lost(typeID=line['typeID'])
                        kill.items_lost_collection.append(item)

                    for line in row['attackers']:
                        attacker = losses.base.classes.attacker(weaponTypeID=line['weaponTypeID'], 
                                                                allianceID=line['allianceID'],
                                                                corporationName=line['corporationName'],
                                                                shipTypeID=line['shipTypeID'],
                                                                characterName=line['characterName'],
                                                                characterID=line['characterID'],
                                                                allianceName=line['allianceName'])

                        kill.attacker_collection.append(attacker)


                    #print('storing ship: %s' % (self.utils.lookup_typename(row['victim']['shipTypeID'])))
                
                    losses.session.add(kill) 
                    losses.session.commit()

            alliances_requested = []        

    def update_pi(self):
        print('updating PI statistics...')

        for system_name in self.config['statistics']['pi_systems']:
            system = self.utils.lookup_system(system_name).__dict__

            for tier in self.config['statistics']['pi_tiers']:
                self.pi_utils.store_prices(tier, system['solarSystemID'])
                
        print('Done')

    def create_databases(self):
        # You must import the metadata file, then connect it to the engine, otherwise
        # it will create a db with no tables. 
        from spearmint_libs.sql import initialize_sql
        from spearmint_libs.sql.losses import ItemsLost, Kills
        from spearmint_libs.sql.users  import Users, Character
        from spearmint_libs.sql.pi     import Pi

        initialize_sql(self.db.engine)



if __name__ == '__main__':
    cli = Command()
