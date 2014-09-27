from spearmint_libs.sql.db_connect import Connect

class User():
    def __init__(self, config):
        self.config = config

        self.db = Connect(self.config['database']['data'])




