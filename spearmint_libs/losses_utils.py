from spearmint_libs.sql.db_connect import Connect
from sqlalchemy import func


class LossesUtils():
    def __init__(self, config):
        self.db = Connect(config['database']['data'])
        self.classes = self.db.base.classes
        

    def oldest_record(self, alliance_ids, kills=True):
        # Get the first killTime recorded
        if kills:
                return self.db.session.query(self.classes.attacker.killTime).filter(self.classes.attacker.allianceID.in_(alliance_ids)).order_by(self.classes.attacker.killTime.asc()).first().killTime

        return self.db.session.query(self.classes.kills.killTime).filter(self.classes.kills.allianceID.in_(alliance_ids)).order_by(self.classes.kills.killTime.asc()).first().killTime 



    def query_total(self, alliance_ids, characterID=None, days_ago=1000, kills=True):
        if kills and characterID:
            return self.db.session.query(self.classes.attacker.shipTypeID, func.count(self.classes.attacker.shipTypeID)).group_by(self.classes.attacker.shipTypeID).filter(
                    self.classes.attacker.allianceID.in_(alliance_ids)).filter(self.classes.attacker.killTime > days_ago).filter_by(characterID=characterID).all()
           
        if kills:
            return self.db.session.query(self.classes.attacker.shipTypeID, func.count(self.classes.attacker.shipTypeID)).group_by(self.classes.attacker.shipTypeID).filter(
                    self.classes.attacker.allianceID.in_(alliance_ids)).filter(self.classes.attacker.killTime > days_ago).all()

        if characterID:
            return self.db.session.query(self.classes.kills.shipTypeID, func.count(self.classes.kills.shipTypeID)).filter(
                    self.classes.kills.killTime > days_ago).group_by(self.classes.kills.shipTypeID).filter_by(characterID=characterID).filter(
                            self.classes.kills.allianceID.in_(alliance_ids)).all()

        return self.db.session.query(self.classes.kills.shipTypeID, func.count(self.classes.kills.shipTypeID)).group_by(self.classes.kills.shipTypeID).filter(self.classes.kills.killTime > days_ago).filter(
                self.db.base.classes.kills.allianceID.in_(alliance_ids)).all()


    def query(self, alliance_ids, characterID=None, shipTypeID=None, days_ago=1000, kills=True):

        if kills:
            if characterID and shipTypeID:
                return self.db.session.query(self.classes.attacker).filter(self.classes.attacker.killTime > days_ago).filter_by(characterID=characterID, shipTypeID=shipTypeID).filter(
                        self.classes.attacker.allianceID.in_(alliance_ids)).all()

            if characterID:
                return self.db.session.query(self.classes.attacker).filter(self.classes.attacker.killTime > days_ago).filter_by(characterID=characterID).filter(
                        self.classes.attacker.allianceID.in_(alliance_ids)).all()

            if shipTypeID:
                return self.db.session.query(self.classes.attacker).filter(self.classes.attacker.killTime > days_ago).filter_by(shipTypeID=shipTypeID).filter(
                        self.classes.attacker.allianceID.in_(alliance_ids)).all()

            else:
                return self.db.session.query(self.classes.attacker).filter(self.classes.attacker.killTime > days_ago).filter(
                        self.classes.attacker.allianceID.in_(alliance_ids)).all()



        if characterID and shipTypeID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(characterID=characterID, shipTypeID=shipTypeID).filter(
                    self.classes.kills.allianceID.in_(alliance_ids)).all()

        if characterID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(characterID=characterID).filter(
                    self.classes.kills.allianceID.in_(alliance_ids)).all()

        if shipTypeID:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter_by(shipTypeID=shipTypeID).filter(
                    self.classes.kills.allianceID.in_(alliance_ids)).all()
   
        else:
            return self.db.session.query(self.classes.kills).filter(self.classes.kills.killTime > days_ago).filter(
                self.classes.kills.allianceID.in_(alliance_ids)).all()

