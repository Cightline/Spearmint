import evelink.api

import main
import datetime

import plotly.plotly as py
from plotly.graph_objs import *

py.sign_in('username', 'password')

config = main.app.config

eve = evelink.eve.EVE()

corp_api = evelink.api.API(api_key=(config['corp_api']['key'], config['corp_api']['code']))
corp     = evelink.corp.Corp(corp_api)

x = []
y = []

def format_time(timestamp):
    return datetime.datetime.utcfromtimestamp(timestamp)

for row in corp.wallet_journal()[0]:
    x.append(format_time(row['timestamp']))
    y.append(row['balance'])


data = Data([Scatter(x=x, y=y, name='Balance')])
plot_url = py.plot(data, filename='corp-wallet-balance')
