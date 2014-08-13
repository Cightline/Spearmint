import configparser
import os
import logging
import copy
import json
from functools import wraps

from flask import Flask, render_template, request, redirect, session, url_for, escape, Response

from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required

from flask_wtf import Form, RecaptchaField
from wtforms import TextField

from werkzeug.contrib.cache import SimpleCache


import evelink.api

from spearmint_libs.utils import Utils
from spearmint_libs.pi    import Pi
from spearmint_libs.auth  import Auth
from spearmint_libs.user  import db, User, Character


with open("config.json") as cfg:
    config = json.loads(cfg.read())

assert(config)


eve = evelink.eve.EVE()

app = Flask(__name__)
app.config.update(config)

#app.config['DEBUG'] = True


app.config['SECRET_KEY']              = os.urandom(1488)
app.config['SQLALCHEMY_DATABASE_URI'] = app.config['database']['uri']


db.init_app(app)

login_manager  = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

logging.basicConfig(filename=app.config['general']['log_path'], level=logging.DEBUG)

# Setup the corp api object and get the corp ID
corp_api = evelink.api.API(api_key=(app.config['corp_api']['key'], app.config['corp_api']['code']))
corp     = evelink.corp.Corp(corp_api)
app.config['corp_id']  = corp.corporation_sheet()[0]['id']


utils = Utils(app.config)
pi    = Pi(app.config, utils)
cache = SimpleCache()


class RegisterForm(Form):
    keyid = TextField('KeyID')
    code  = TextField('Code')


    recaptcha = RecaptchaField()

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

@login_manager.user_loader 
def load_user(id):
    query = User.query.filter_by(email=id).first()
    return query or None


@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':

        if check_auth(request.form.get('email'), request.form.get('password')):
          
            to_login = load_user(request.form.get('email'))
            
            if login_user(to_login):
                logging.info('[login] logged in: %s' % (current_user.email))
                return render_template('info.html', info='Successfully logged in as %s'  % (to_login.email))

        else:
            return render_template('info.html', info='Incorrect email/password combination')

    return render_template('login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if current_user.is_authenticated():
        logout_user()
        return render_template('info.html', info='Successfully logged out')

    return render_template('info.html', info='You are not logged in')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():

    if request.method == 'POST':

        logging.info('[register] request.form: %s' % (request.form))

        api = evelink.api.API(api_key=(request.form.get('keyid'), request.form.get('code')))
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
                if char_copy[c]['corp']['id'] != app.config['corp_id']:
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

    
    
    
    return render_template('register.html', form=RegisterForm())


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


@app.route('/pi_statistics/<int:tier>', methods=['GET', 'POST'])
def pi_statistics(tier):

    results = {}
    systems = ['jita']

    for system_name in systems:
        system = utils.search_system(system_name)
        data = pi.get_prices(tier, system['solarSystemID'])

        if data:
            results[system['solarSystemName']] = data


    return render_template('pi_statistics.html', results=results)


@app.route('/corp', methods=['GET'])
@login_required
def corp_index():
    return render_template('corp_index.html')


@app.route('/corp/standings', methods=['GET'])
@login_required
def corp_standings():

    return render_template('corp_standings.html', standings=corp.npc_standings())


@app.route('/corp/wallet_transactions',  methods=['GET'])
@login_required
def corp_transactions():

    return render_template('corp_transactions.html', wallet_transactions=corp.wallet_transactions())



if __name__ == '__main__':
    app.run()
