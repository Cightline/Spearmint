from spearmint_libs.sql.db_connect import Connect
from sqlalchemy import func


class LossesUtils():
    def __init__(self, config):
        self.db = Connect(config['database']['data'])
        self.classes = self.db.base.classes
        

    def oldest_record(self):
        # Get the first killTime recorded
        return self.db.session.query(self.classes.kills).order_by(self.classes.kills.killTime.asc()).first().killTime or  None


    def query_total(self, alliance_ids, characterID=None, days_ago=1000):
        if characterID:
            return self.db.session.query(self.classes.kills.shipTypeID, func.count(self.classes.kills.shipTypeID)).filter(
                    self.classes.kills.killTime > days_ago).group_by(self.classes.kills.shipTypeID).filter_by(characterID=characterID).filter(
                            self.classes.kills.allianceID.in_(alliance_ids)).all()

        return self.db.session.query(self.classes.kills.shipTypeID, func.count(self.classes.kills.shipTypeID)).group_by(self.classes.kills.shipTypeID).filter(self.classes.kills.killTime > days_ago).filter(
                self.db.base.classes.kills.allianceID.in_(alliance_ids)).all()


    def query(self, alliance_ids, characterID=None, shipTypeID=None, days_ago=1000):
        if characterID and shipTypeID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(characterID=characterID, shipTypeID=shipTypeID).filter(
                    self.classes.kills.allianceID.in_(alliance_ids)).all()

        elif characterID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(characterID=characterID).filter(
                    self.classes.kills.allianceID.in_(alliance_ids)).all()

        elif shipTypeID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(shipTypeID=shipTypeID).filter(
                    self.classes.kills.allianceID.in_(alliance_ids)).all()
   
        else:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter(
                self.classes.kills.allianceID.in_(alliance_ids)).all()

