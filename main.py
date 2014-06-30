from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from flask import url_for
from flask import escape
from flask.ext.sqlalchemy import SQLAlchemy



import os
from libs.utils import Utils
from libs.pi    import Pi

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = '%s/user_data.db' % (os.getcwd())
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html')


#def index():
#    if 'username' in session:
#        return 'Logged in as %s' % escape(session['username'])
#
#    else:
#        return 'You are not logged in'

@app.route('/pi_lookup_form')
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
    app.debug = True
    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run()
