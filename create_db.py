import main


with main.app.app_context():
    main.db.create_all()

from spearmint_libs import pi
p = pi.Pi(main.app.config, main.utils)
pi.Base.metadata.create_all(p.store_engine)
