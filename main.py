import configparser
import os
import logging

from flask import Flask, render_template, request, redirect, session, url_for, \
                  escape

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login      import LoginManager
from flask.ext.security   import Security, SQLAlchemyUserDatastore, UserMixin, \
                                 RoleMixin, login_required

from werkzeug.security import generate_password_hash, check_password_hash

from libs.utils import Utils
from libs.pi    import Pi

import evelink.api

config = configparser.ConfigParser()
config.read('%s/settings.cfg' % (os.getcwd()))


eve = evelink.eve.EVE()

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = config.get('general', 'secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = config.get('database', 'uri')
db = SQLAlchemy(app)

login_manager  = LoginManager()
login_manager.init_app(app)

CORP_ID = config.get('corp', 'id')

logging.basicConfig(filename=config.get('general', 'log_path'), level=logging.DEBUG)




roles_users = db.Table('roles_users', 
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id_  = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))




class Auth(object):
    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

class User(db.Model):
    id_      = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(255))
    active   = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles    = db.relationship('Role', secondary=roles_users,
                                backref=db.backref('users', lazy='dynamic'))
    username = db.Column(db.String(80),  unique=True)

    def __init__(self, username, email):
        self.username = username
        self.email    = email

    def __repr__(self):
        return '%r' % self.username

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)


@login_manager.user_loader 
def load_user(userid):
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST', 'GET'])
def register():

    if request.method == 'POST':

        logging.info('[register] request.form: %s' % (request.form))

        api = evelink.api.API(api_key=(request.form.get('register_keyid'), request.form.get('register_code')))
        account = evelink.account.Account(api)

        try:
            characters = account.characters()
        except Exception as ex: 
            logging.warning('[register] exception: %s' % (ex))
            return render_template('info.html', info="It dosen't seem like you correctly entered your API")


        if characters.result:

            # Remove characters that are not in the corp.
            for character in characters.result:
                if characters.result[character]['corp']['id'] != CORP_ID:
                    del characters.result[character]
               
            # Check to see if we still have any characters left. 
            if characters.result:
                logging.info('[register] characters.result: %s' % characters.result)
                session['characters'] = characters.result
                
                return redirect(url_for('confirm_register'))

            else:
                return render_template('info.html', info='None of your characters are in the corporation')


    return render_template('register.html')


@app.route('/confirm_register', methods=['POST', 'GET'])
def confirm_register():
    if request.method == 'POST': 
        # debug 
        print('[confirm_register] %s' % (request.form))

      
        auth = Auth(request.form.get('register_email'), request.form.get('register_password'))

        logging.info('[confirm_register] password hash: %s' % (auth.pw_hash))

        # Make sure user isn't already in the db. 
        query = User.query.filter_by(username=request.form.get('register_email')).first()

        if request.form.get('register_email') == query.username:
            return render_template('info.html', info='You have already registered')
        

        # Add the user to the db and generate the password hash.
        user = User(request.form.get('register_email'), auth.pw_hash)
        db.session.add(user)
        db.session.commit()


        return render_template('submitted_register.html')



    return render_template('confirm_register.html', characters=session['characters'])


@app.route('/pi_lookup_form')
@login_required
def pi_lookup_form():
    return render_template('pi_lookup_form.html')


@app.route('/pi_lookup', methods=['GET'])
def pi_lookup():
    utils = Utils()
    pi    = Pi()

    system = utils.search_system(request.args.get('system').strip())
    items  = pi.lookup_prices(int(request.args.get('tier')),
                                  system=system[0][1])

    keys = list(items.keys())
    keys.sort()
    keys.reverse()

    return render_template('pi_lookup.html', system=system[0][0],
                                             tier=request.args.get('tier'),
                                             keys=keys,
                                             items=items)



@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))


    else:
        return '''<form action='' method='post'>
                  <p><input type=text name=username>
                  <p><input type=submit value=login>
                  </form>''' 
    






if __name__ == '__main__':
    app.run()
