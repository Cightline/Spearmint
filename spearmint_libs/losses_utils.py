from spearmint_libs.sql.db_connect import Connect


class LossesUtils():
    def __init__(self, config):
        self.db = Connect(config['database']['data'])
        self.classes = self.db.base.classes
        

    def oldest_record(self):
        # Get the first killTime recorded
        return self.db.session.query(self.classes.kills).order_by(self.classes.kills.killTime.asc()).first().killTime or  None

    
    def query(self, characterID=None, shipTypeID=None, days_ago=1000):
        if characterID and shipTypeID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(characterID=characterID, shipTypeID=shipTypeID).all()

        elif characterID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(characterID=characterID).all()

        elif shipTypeID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(shipTypeID=shipTypeID).all()
   
        else:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).all()

