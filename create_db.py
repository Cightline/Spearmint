import main


with main.app.app_context():
    main.db.create_all()

from spearmint_libs import pi
print('pi_db_path: ',main.pi_db_path)
p = pi.Pi(main.ccp_db_path, main.pi_db_path)
pi.Base.metadata.create_all(p.store_engine)
