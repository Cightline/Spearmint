import main
from spearmint_libs import pi
from spearmint_libs import utils


with main.app.app_context():
    main.db.create_all()

pi = pi.Pi(main.ccp_db_path, main.pi_db_path)
utils = utils.Utils(main.ccp_db_path)

systems = ['jita', 'amarr']
tiers   = [1,2,3]

for system_name in systems:
    system = utils.search_system(system_name)
    print(system)
    for tier in tiers:
        pi.store_prices(tier, system['solarSystemID'])


