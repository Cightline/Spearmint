import configparser
import os
import logging
import copy
import json
import datetime
import hashlib

from urllib.parse import quote
from functools    import wraps
from flask import Flask, render_template, request, redirect, session, url_for, escape, Response 
from flask.ext.login import LoginManager, login_user, logout_user, current_user, login_required
from flask.ext.cache import Cache

from flask_wtf import Form, RecaptchaField
from wtforms import TextField

from werkzeug.security import generate_password_hash, check_password_hash

import evelink.api
import requests

from spearmint_libs.utils import Utils, format_time, format_currency, generate_code
from spearmint_libs.pi_utils    import PiUtils
from spearmint_libs.losses_utils import LossesUtils
from spearmint_libs.auth  import Auth
from spearmint_libs.user_utils  import User
from spearmint_libs.emailtools import EmailTools


with open("config.json") as cfg:
    config = json.loads(cfg.read())

assert(config)


db_path = config['database']['data'].split(':')[-1]

if not os.path.exists(db_path):
    print('Database at %s does not exist' % (db_path))
    exit()

eve = evelink.eve.EVE()
emailtools = EmailTools(config)

app = Flask(__name__)
app.config.update(config)

app.config['DEBUG'] = False
app.config['SECRET_KEY']              = os.urandom(1488)
app.config['SQLALCHEMY_DATABASE_URI'] = app.config['database']['data']
app.config['log_path'] = '%s/log' % (app.config['general']['base_dir'])

login_manager  = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

logging.basicConfig(filename=app.config['log_path'], level=logging.DEBUG)

# Setup the corp api object and get the corp ID
corp_api = evelink.api.API(api_key=(app.config['corp_api']['key'], app.config['corp_api']['code']))
corp     = evelink.corp.Corp(corp_api)
app.config['corp_id']  = corp.corporation_sheet()[0]['id']


utils =  Utils(app.config)
losses = LossesUtils(app.config)
pi    =  PiUtils(app.config, utils)
cache =  Cache(app,config={'CACHE_DIR':'%s/cache' % (app.config['general']['base_dir']), 
                           'CACHE_DEFAULT_TIMEOUT':10000000000000000,
                           'CACHE_TYPE': app.config['general']['cache_type']})




@cache.memoize()
def character_name_from_id(id_):
    return eve.character_name_from_id(id_)[0]

# Insecure?
@cache.memoize()
def character_id_from_name(name):
    return eve.character_ids_from_names([name])[0][name]

@cache.memoize()
def corp_name_from_character_id(id_):
    corp_name = eve.affiliations_for_characters(id_)
    return corp_name[0][id_]['name']


@cache.memoize()
def alliance_id_from_corp_id(corp_id):
    sheet = corp.corporation_sheet(corp_id=corp_id)
    
    return sheet[0]['alliance']['name']



app.jinja_env.filters['format_time'] = format_time
app.jinja_env.filters['format_currency'] = format_currency
app.jinja_env.filters['character_name_from_id'] = character_name_from_id
app.jinja_env.filters['corp_name_from_character_id'] = corp_name_from_character_id
app.jinja_env.filters['alliance_id_from_corp_id'] = alliance_id_from_corp_id
app.jinja_env.filters['lookup_typename'] = utils.lookup_typename
app.jinja_env.filters['quote'] = quote

user = User(config)

class RegisterForm(Form):
    keyid = TextField('KeyID')
    code  = TextField('Code')

    recaptcha = RecaptchaField()


class UserChangePassword(Form):
    password    = TextField('Password')
    verify_pass = TextField('Verify Password')


def check_auth(email, password):
    query = user.lookup_user(email)

    if query:
        if check_password_hash(query.password, password) == True:
            logging.info('[check_auth] correct password for: %s' % (query.email))
            return True

        else:
            logging.info('[check_auth] incorrect password for: %s' % (query.email))
    else:
        logging.info("[check_auth] couldn't find %s for authentication" % (email))

    return False


@login_manager.user_loader 
def load_user(id):
    return user.load_user(id) or None


def info(info, home_button=False):
    return render_template('info.html', info=info, home_button=home_button)

@app.route('/login', methods=['POST','GET'])
def login():
    if current_user.is_authenticated():
        return render_template('info.html', info='You are already logged in')
    
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        
        if check_auth(email, password) != True:
            return render_template('info.html', info='Incorrect email or password')


        to_login = load_user(email)

        if not to_login:
            return render_template('info.html', info='unable to log you in')
            
        if login_user(to_login):
            logging.info('[login] logged in: %s' % (current_user.user.email))
                
            # Fix this, it needs to actually redirect. 
            next_page = request.form.get('next')

            if next_page:
                return redirect(next_page)

            else:
                return redirect('/')

        else:
            logging.info('[login] unable to login: %s' % (to_login.__unicode__()))

    return render_template('login.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if current_user.is_authenticated():
        logout_user()
        return render_template('info.html', info='Successfully logged out', home_button=True)

    return render_template('info.html', info='You are not logged in')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/register', methods=['POST', 'GET'])
def register():

    if request.method == 'POST':

        logging.info('[register] request.form: %s' % (request.form))

        keyid = request.form.get('keyid')
        code  = request.form.get('code')

        api = evelink.api.API(api_key=(keyid, code))
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
            if not characters.result:
                return render_template('info.html', info='None of your characters are in the corporation')
                
            logging.info('[register] characters.result: %s' % characters.result)

            session['characters']  = characters.result
            session['api_code']    = code
            session['api_key_id']  = keyid

            return redirect(url_for('confirm_register'))

    return render_template('register.html', form=RegisterForm())


@app.route('/confirm_register', methods=['POST', 'GET'])
def confirm_register():
    
    if 'api_key_id' not in session or 'api_code' not in session or 'characters' not in session:
        return render_template('info.html', info='Missing API, restart the registration.')
    
    if request.method == 'POST': 

        auth  = Auth(request.form.get('register_email'), request.form.get('register_password'))
        email = request.form.get('register_email')
        
        logging.info('[confirm_register] password hash: %s' % (auth.pw_hash))

        # Make sure user isn't already in the db. 
        query = user.lookup_user(email)

        if query:
            if email == query.email:
                return render_template('info.html', info='You have already registered')

        # Add the user to the db and generate the password hash.
        activation_code = generate_code()
        
        user.add_user(
                email=email, 
                password=auth.pw_hash,
                api_key_id=session['api_key_id'],
                api_code=session['api_code'],
                active=False,
                activation_code=activation_code)
     
        for character_id in session['characters']:
            logging.info('Adding character %s to %s, result %s' % (character_id, email, user.add_character(email, character_id)))

        activation_link = 'http://%s/activate_account?activation_code=%s&email=%s' % (config['general']['hostname'], activation_code, email)

        try:
            emailtools.send_email(to=email, 
                                  subject='Activate your account', 
                                  body=activation_link)

        except ConnectionRefusedError:
            logging.warn('error sending email, make sure the MTA is runnnig')

            return info('Unable to send email, contact the admin', home_button=True)

        return render_template('submitted_register.html')



    return render_template('confirm_register.html', characters=session['characters'])


@app.route('/reset_password', methods=['POST','GET'])
def email_reset_password():
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            return render_template('info.html', info='Missing email')

        query = user.lookup
        if not query:
            return render_template('info.html', info='User not found')

        recovery_code = generate_code() 
        query.recovery_code = recovery_code
        query.recovery_timestamp = datetime.datetime.now()

        db.session.commit()

        recovery_link = 'http://%s/password_recovery?recovery_code=%s&email=%s' % (config['general']['hostname'], recovery_code, email)

        emailtools.send_email(to=email,
                              subject='Password recovery',
                              body=recovery_link)

        return render_template('info.html', info='Recovery email has been sent')

    return render_template('reset_password.html')


@app.route('/password_recovery', methods=['POST', 'GET'])
def reset_password():
    if request.method == 'GET':
        email         = request.args.get('email')
        recovery_code = request.args.get('recovery_code')
   
        if not email or not recovery_code:
            return render_template('info.html', info='Invalid recovery code or email')

        query = User.query.filter_by(email=email).first()

        # Gotta be pretty 1337 to get this far
        if not query:
            return render_template('info.html', info='Account not found')

        time_elapsed = (datetime.datetime.now() - query.recovery_timestamp) / 3600.0 
        if recovery_code == query.recovery_code:
            login_user(query)
            return redirect(url_for('user/index'))

    return render_template('password_recovery.html')



@app.route('/user/index', methods=['POST', 'GET'])
@login_required
def user_settings():
    return render_template('user/index.html')


@app.route('/user/settings/password', methods=['POST', 'GET'])
@login_required
def user_change_password():
    if request.method == 'POST':
        password        = request.form.get('password')
        verify_password = request.form.get('verify_password')

        if not len(password) and not len(verify_password):
            return render_template('info.html', info='No password entered')
            
        if password != verify_password:
            return render_template('info.html', info='Passwords do not match')
            
        auth = Auth(current_user.user.email, password)
        current_user.user.password = auth.pw_hash
        db.session.commit()

        return render_template('info.html', info='Password successfully updated.')

    return render_template('user/settings/password.html', form=UserChangePassword())


@app.route('/activate_account', methods=['GET'])
def activate_account():
    email = request.args.get('email')
    activation_code  = request.args.get('activation_code')

    query = User.query.filter_by(email=email).first()  

    if not query or not email or not activation_code:
        return render_template('info.html', info='There is an issue trying to activate your account, please contact the admin.')

    # See if the activation code matches, and if it does "activate" the account, and set the previously used
    # code to 'NULL'
    if activation_code == query.activation_code and query.activation_code != 'NULL':
        query.activation_code = 'NULL'
        query.active = True
        query.activation_timestamp = datetime.datetime.now()
        db.session.commit()

        return render_template('info.html', info='Your account has been activated')
    
    return render_template('info.html', info='Invalid activation code or email')

@app.route('/statistics/pi/<int:tier>', methods=['GET', 'POST'])
@login_required
def statistics_pi(tier):

    results = {}
    systems = ['jita']

    for system_name in systems:
        system = utils.lookup_system(system_name)
        data = pi.get_prices(tier, system.solarSystemID)

        if data:
            results[system.solarSystemName.lower()] = {"data":data, "cached_time":data[0].date}

    return render_template('statistics/pi.html', results=results)


@app.route('/corp/index', methods=['GET'])
@login_required
def corp_index():
    return render_template('corp/index.html')


@app.route('/corp/standings', methods=['GET'])
@login_required
def corp_standings():
    return render_template('corp/standings.html', standings=corp.npc_standings())


@app.route('/corp/wallet_transactions',  methods=['GET'])
@login_required
def corp_transactions():
    return render_template('corp/wallet_transactions.html', wallet_transactions=corp.wallet_transactions())

@app.route('/corp/contracts', methods=['GET'])
@login_required
def corp_contracts():
    contracts = corp.contracts()[0]

    return render_template('corp/contracts.html', contracts=contracts)



@app.route('/statistics/ships_lost_details', methods=['GET'])
@login_required
def statistics_ship_losses_details():
    days = 20
    character_id = None

    if 'days' in request.args:
        try:
            days = int(request.args.get('days'))
        except:
            return info('Incorrect amount of days entered')

    if 'ship' in request.args:
        ship_name = request.args.get('ship')
        ship_id   = utils.lookup_typeid(ship_name)

        if not ship_id:
            info('Ship not found') 
    if 'character' in request.args:
        character = request.args.get('character')
        if character != 'all':
            try:
                character_id = int(character_id_from_name(request.args.get('character')))
            except:
                return info('Unable to find character')


    kills = request.args.get('kills')

    if kills == 'True':
        kills = True

    elif kills == 'False':
        kills = False

    else:
        kills = True

    coalition = request.args.get('coalition')

    if 'coalition' not in request.args:
        coalition = list(config['coalitions'].keys())[0]

    if coalition in config['coalitions']:
        alliance_ids = config['coalitions'][coalition]

    else:
        return info('Incorrect coalition')

    current_time = datetime.datetime.utcnow() 
    days_ago     = current_time - datetime.timedelta(days=days) 
    
    query = losses.query(alliance_ids, characterID=character_id, shipTypeID=ship_id, days_ago=days_ago, kills=kills)
    
    return render_template('statistics/ship_losses_details.html', coalition=coalition, data=query, ship_name=ship_name, ship_id=ship_id, kills=kills)


@app.route('/statistics/ships_lost', methods=['GET'])
@login_required
def statistics_ship_losses():
    current_time = datetime.datetime.utcnow() 
    days         = 20
    character_id = None
    character    = None
    total_ships_lost = 0
    ships_lost   = {}

    if 'days' in request.args:
        try:
            days = int(request.args.get('days'))

        except:
            return info('Incorrect amount of days entered')

    if 'character' in request.args:
            character    = request.args.get('character')

            if character != 'all':
                try:
                    character_id = int(character_id_from_name(character)) or None

                except:
                    return info('Unable to find character')


    coalition      = request.args.get('coalition')
    kills          = request.args.get('kills')

    if kills == 'True':
        kills = True

    elif kills == 'False':
        kills = False

    else:
        kills = True


    if 'coalition' not in request.args:
        coalition  = list(config['coalitions'].keys())[0]
    
    if coalition in config['coalitions']:
        alliance_ids = config['coalitions'][coalition]

    else:
        return info('Incorrect coalition')


    days_ago      = current_time - datetime.timedelta(days=days) 


   
    if character_id:
            query = losses.query_total(alliance_ids, days_ago=days_ago, characterID=character_id, kills=kills)

    else:
        query = losses.query_total(alliance_ids, days_ago=days_ago, kills=kills)

    oldest_record = losses.oldest_record(alliance_ids, kills)
    
    if oldest_record:
        days_stored   = current_time - oldest_record

    else:
        days_stored = 'N/A'

    for ship in query:

        ship_name = utils.lookup_typename(ship[0]) or 'NA'
        total_ships_lost += ship[1]

        if ship_name not in ships_lost:
            ships_lost[ship_name] = ship[1]


    return render_template('statistics/ship_losses.html',  config_coalitions=config['coalitions'], 
                                                           coalition=coalition, 
                                                           ships_lost=ships_lost, 
                                                           days=days, 
                                                           oldest_record=oldest_record, 
                                                           days_stored=days_stored.days, 
                                                           character=character, 
                                                           total_ships_lost=total_ships_lost,
                                                           kills=kills)



if __name__ == '__main__':
    app.run()
