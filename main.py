import configparser
import os
import logging
import copy
from functools import wraps

from flask import Flask, render_template, request, redirect, session, url_for, \
                  escape, Response

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login      import LoginManager, login_user, current_user

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
app.config['SQLALCHEMY_DATABASE_URI'] = str(config.get('database', 'uri'))
db = SQLAlchemy(app)

login_manager  = LoginManager()
login_manager.init_app(app)

CORP_ID = int(config.get('corp', 'id'))

logging.basicConfig(filename=config.get('general', 'log_path'), level=logging.DEBUG)


class Auth(object):
    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)


class Character(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer)
    user_id      = db.Column(db.Integer, db.ForeignKey('user.id'))

class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True)
    password   = db.Column(db.String(255))
    api_code   = db.Column(db.String(255))
    api_key_id = db.Column(db.String(255))
    characters = db.relationship('Character', backref='user', lazy='dynamic')




db.create_all()
db.session.commit()

def check_auth(email, password):
    query = User.query.filter_by(email=email).first()

    if query:
        a = Auth(email, password)
       
        if a.check_password(password):
            logging.info('[check_auth] user: %s logged in' % (query.email))
            return True

        else:
            logging.info('[check_auth] incorrect password for: %s' % (query.email))

    else:
        logging.info("[check_auth] couldn't find %s for authentication" % (email))

    return False

def authenticate():
    return render_template('login.html')
    #return Response('Could not verify your access level for that URL. \n'
    #                'You have to login with proper credentials', 401, {'WWW-Authenticate':'Basic realm="Services Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()

        return f(*args, **kwargs)

    return decorated

@login_manager.user_loader 
def load_user(email):
    query = User.query.filter_by(email=email).first()
    return query or None


@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':

        if check_auth(request.form.get('email'), request.form.get('password')):
            login_user(load_user(request.form.get('email')))
            return render_template('info.html', info='Successfully logged in')


        else:
            return render_template('info.html', info='Incorrect email/password combination')

    return render_template('login.html')


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
            # Store in seperate dictionary so I can edit it. 
            char_copy = copy.deepcopy(characters.result)

            # Remove characters that are not in the corp.
            for c in char_copy:
                if char_copy[c]['corp']['id'] != CORP_ID:
                    # Remove from the original dictionary.
                    logging.info('[register] removing character: %s' % (characters.result[c]))
                    del characters.result[c]
               
            # Check to see if we still have any characters left. 
            if characters.result:
                logging.info('[register] characters.result: %s' % characters.result)

                session['characters'] = characters.result
                session['api_code']   = request.form.get('register_code')
                session['api_key_id']  = request.form.get('register_keyid')

                return redirect(url_for('confirm_register'))

            else:
                return render_template('info.html', info='None of your characters are in the corporation')


    return render_template('register.html')


@app.route('/confirm_register', methods=['POST', 'GET'])
def confirm_register():
    if request.method == 'POST': 
      
        auth = Auth(request.form.get('register_email'), request.form.get('register_password'))

        logging.info('[confirm_register] password hash: %s' % (auth.pw_hash))

        # Make sure user isn't already in the db. 
        query = User.query.filter_by(email=request.form.get('register_email')).first()

        if query:
            if request.form.get('register_email') == query.email:
                return render_template('info.html', info='You have already registered')

     

        # Add the user to the db and generate the password hash.
        user = User(email=request.form.get('register_email'), 
                    password=auth.pw_hash,
                    api_key_id=session['api_key_id'],
                    api_code=session['api_code'])
     
        db.session.add(user)
        db.session.commit()

        
        for c in session['characters']:
            db.session.add(Character(character_id=c, user=user))
            db.session.commit() 



        return render_template('submitted_register.html')



    return render_template('confirm_register.html', characters=session['characters'])


@app.route('/pi_lookup_form')
@requires_auth
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






if __name__ == '__main__':
    app.run()
