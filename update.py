import argparse
import json
import datetime

import requests

from sqlalchemy     import create_engine
from sqlalchemy.orm import Session, sessionmaker

from spearmint_libs.pi     import Pi
from spearmint_libs.utils  import Utils, format_time
from spearmint_libs.losses import Kills, ItemsLost

import evelink



class Command():
    def __init__(self):
        self.config = self.read_config()
        self.utils  = Utils(self.config)
        self.pi     = Pi(self.config, self.utils)
        self.eve    = evelink.eve.EVE()
        self.corp_api = evelink.api.API(api_key=(self.config['corp_api']['key'], self.config['corp_api']['code']))
        self.corp     = evelink.corp.Corp(self.corp_api)


        self.losses_engine = create_engine(self.config['database']['losses'], convert_unicode=True)


        parser = argparse.ArgumentParser()
        parser.add_argument('--pi',        help='update the PI cache',  action='store_true')
        parser.add_argument('--losses',    help='update the items and ships that have been destroyed', action='store', type=int)
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
        session = sessionmaker(bind=self.losses_engine)
        # Why does "session()"  seem so confusing
        losses_session = session()
        losses_session._model_changes = {}

        items_lost  = {}
        alliance_id = self.corp.corporation_sheet()[0]['alliance']['id']

        if self.args.start:
            start_page = self.args.start

        else:
            start_page = 0

        for count in range(start_page, self.args.losses):
            print('Page %s of %s' % (count, self.args.losses))

            kb_url =  'https://zkillboard.com/api/kills/allianceID/%s/page/%s/losses/' % (alliance_id, count)
            
            data = json.loads(requests.get(kb_url).text)
          
            for row in data:
                # I'm putting row_count up here because its possible to already have the kill in the db. 

                #self.display_completion(row_count)
                # 'killTime': '2014-09-19 21:27:00'
                time_format = '%Y-%m-%d %H:%M:%S'
                kill_time = datetime.datetime.strptime(row['killTime'], time_format)
                kill_id   = row['killID']

                query = losses_session.query(Kills).filter_by(killID=kill_id).first()

                if query:
                    #print('killID already exists, skipping')
                    continue
               
                kill = Kills(killID=kill_id, 
                             shipTypeID=row['victim']['shipTypeID'], 
                             killTime=kill_time,
                             characterID=row['victim']['characterID'])

                for line in row['items']:
                    #print('storing item: %s' % (self.utils.lookup_typename(line['typeID'])))
                    kill.items.append(ItemsLost(typeID=line['typeID']))


                #print('storing ship: %s' % (self.utils.lookup_typename(row['victim']['shipTypeID'])))
                
                losses_session.add(kill) 
                losses_session.commit()

            

    def update_pi(self):
        print('updating PI statistics...')

        for system_name in self.config['statistics']['pi_systems']:
            system = self.utils.lookup_system(system_name).__dict__

        for tier in self.config['statistics']['pi_tiers']:
            self.pi.store_prices(tier, system['solarSystemID'])
                
        print('Done')

    def create_databases(self):
        # Losses
        Kills().metadata.create_all(self.losses_engine)

       


if __name__ == '__main__':
    cli = Command()
