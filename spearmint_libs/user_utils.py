from spearmint_libs.sql.db_connect import Connect

class LoadUser():
    def __init__(self, user):
        self.user = user
        self.email = user.email

    
    def __unicode__(self):
        return self.user.email

    def is_authenticated(self):
        return True

    def is_active(self):
        return True
        #return self.user.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.user.email

    

class User():
    def __init__(self, config):
        self.config = config

        self.db = Connect(self.config['database']['data'])


    def load_user(self, email):
        q = self.lookup_user(email)

        if not q:
            return False

        return LoadUser(self.lookup_user(email))

    def lookup_user(self, email):
        q = self.db.session.query(self.db.base.classes.users).filter_by(email=email).first()

        if not q:
            return False

        return q


    def add_user(self, **kwargs):
        new_user = self.db.base.classes.users(**kwargs)

        self.db.session.add(new_user)
        self.db.session.commit()


    def add_character(self, email, character_id):

        q = self.lookup_user(email)

        if not q:
            return False

        new_character = self.db.base.classes.characters(character_id=character_id)
        q.characters_collection.append(new_character)
        self.db.session.add(q)
        self.db.session.commit()






