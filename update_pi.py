import main
from spearmint_libs import pi
from spearmint_libs import utils


with main.app.app_context():
    main.db.create_all()

utils = utils.Utils(main.app.config)
pi = pi.Pi(main.app.config, utils)

systems = ['jita', 'amarr']
tiers   = [1,2,3]

for system_name in systems:
    system = utils.search_system(system_name)
    for tier in tiers:
        pi.store_prices(tier, system.solarSystemID)


