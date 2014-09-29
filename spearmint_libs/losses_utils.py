from spearmint_libs.sql.db_connect import Connect
from sqlalchemy import func


class LossesUtils():
    def __init__(self, config):
        self.db = Connect(config['database']['data'])
        self.classes = self.db.base.classes
        

    def oldest_record(self):
        # Get the first killTime recorded
        return self.db.session.query(self.classes.kills).order_by(self.classes.kills.killTime.asc()).first().killTime or  None


    def query_total(self, characterID=None, days_ago=1000):
        if characterID:
            return self.db.session.query(self.classes.kills.shipTypeID, func.count(self.classes.kills.shipTypeID)).filter(
                    self.classes.kills.killTime > days_ago).group_by(self.classes.kills.shipTypeID).filter_by(characterID=characterID).all()

        return self.db.session.query(self.classes.kills.shipTypeID, func.count(self.classes.kills.shipTypeID)).group_by(self.classes.kills.shipTypeID).filter(self.classes.kills.killTime > days_ago).all()


    def query(self, characterID=None, shipTypeID=None, days_ago=1000):
        if characterID and shipTypeID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(characterID=characterID, shipTypeID=shipTypeID).all()

        elif characterID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(characterID=characterID).all()

        elif shipTypeID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(shipTypeID=shipTypeID).all()
   
        else:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).all()

