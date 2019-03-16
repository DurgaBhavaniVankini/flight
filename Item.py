from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, FlightPartner, FlightInfo, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps
from flask import Flask, render_template, \
                  url_for, request, redirect,\
                  flash, jsonify

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('Gclient_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Flight Information System"

'''...................'''
# DataBase
'''...................'''
# Connect to database
engine = create_engine('sqlite:///flightsinfo.db', connect_args={
    'check_same_thread': False}, echo=True)
Base.metadata.bind = engine

# Create session
DBSession = sessionmaker(bind=engine)
session = DBSession()

'''...................'''
# Login Routing
'''...................'''
# Login - Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# GConnect


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code, now compatible with Python3
    request.get_data()
    code = request.data.decode('utf-8')

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('Gclient_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    # Submit request, parse response - Python3 compatible
    h = httplib2.Http()
    response = h.request(url, 'GET')[1]
    str_response = response.decode('utf-8')
    result = json.loads(str_response)

    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo?alt=json"
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 150px; height: 150px;border-radius: 150px; \
                            -webkit-border-radius: 150px;-moz-border-radius: \
                                150px;"> '
    return output


'''JSON APIs to view Flights Information'''


@app.route('/flightpartner/<int:flightpartner_id>/info/JSON')
def flightsJSON(flightpartner_id):
    flightpartner = session.query(FlightPartner).filter_by(
                  id=flightpartner_id).one()
    flights = session.query(FlightInfo).filter_by(
        flightpartner_id=flightpartner_id).all()
    return jsonify(flights=[i.serialize for i in flights])


@app.route('/flightpartner/JSON')
def flightPartnerJSON():
    flightpartners = session.query(FlightPartner).all()
    return jsonify(flightpartners=[s.serialize for s in flightpartners])


# Decorator function for login

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


# User Helper Functions

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        login_session.clear()

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        # return response
        return redirect(url_for('showFlightPartners'))
    else:
        # For whatever reason, the given token was invalid
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


'''...................'''
# Flask Routing
'''...................'''

# Homepage
# Flights Partners View


@app.route('/')
@app.route('/flightpartner/')
def showFlightPartners():
    flightpartners = session.query(FlightPartner).distinct(
          FlightPartner.logo).group_by(FlightPartner.logo)
    if 'username' not in login_session:
        return render_template('mainflightpartners.html',
                               flightpartners=flightpartners)
    else:
        return render_template('flightpartners.html',
                               flightpartners=flightpartners)

# Flights Info View


@app.route('/flightpartner/<int:flightpartner_id>/')
@app.route('/flightpartner/<int:flightpartner_id>/info/')
def showFlightInfo(flightpartner_id):
    flightpartner = session.query(
        FlightPartner).filter_by(id=flightpartner_id).one()
    creator = getUserInfo(flightpartner.user_id)
    flights = session.query(FlightInfo).filter_by(
        flight_id=flightpartner_id).all()
    if 'username' not in login_session or \
       creator.id != login_session.get('user_id'):
        return render_template('partnerview.html', flights=flights,
                               flightpartner=flightpartner, creator=creator)
    else:
        return render_template('flightpartnerview.html', flights=flights,
                               flightpartner=flightpartner, creator=creator)


# Adding New Flight Partner


@app.route('/flightpartner/new/', methods=['GET', 'POST'])
@login_required
def newFlightpartner():
    if request.method == 'POST':
        newFlightpartner = FlightPartner(
            name=request.form['name'], logo=request.form['logo'],
            user_id=login_session['user_id'])
        session.add(newFlightpartner)
        flash('New Flightpartner %s Added Successfully'
              % newFlightpartner.name)
        session.commit()
        return redirect(url_for('showFlightPartners'))
    else:
        return render_template('newFlightPartner.html')

# Adding New Flight Information


@app.route('/flightpartner/<int:flightpartner_id>/info/new/',
           methods=['GET', 'POST'])
def newFlight(flightpartner_id):
    if request.method == 'POST':
        newFlight = FlightInfo(
            source=request.form['source'],
            destination=request.form['destination'],
            time=request.form['time'],
            fare=request.form['fare'],
            flight_id=flightpartner_id,
            user_id=login_session['user_id'])
        session.add(newFlight)
        flash('New Flight Added Successfully')
        session.commit()
        return redirect(url_for('showFlightInfo',
                                flightpartner_id=flightpartner_id))
    else:
        return render_template('newFlight.html')

# Flight Information Edit


@app.route('/flightpartner/<int:flightpartner_id>/info/<int:info_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editFlight(flightpartner_id, info_id):
    editFlight = session.query(FlightInfo).filter_by(id=info_id).one()
    flightpartner = session.query(FlightPartner).filter_by(
                                id=flightpartner_id).one()
    if login_session['user_id'] != flightpartner.user_id:
        return "<script>function myFunction()"
        "{alert('You are not authorized to edit"
        "flights information to this"
        "Flightpartner. Please create your own"
        "Flightpartner in order to"
        "edit flights');}"
        "</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['source']:
            editFlight.source = request.form['source']
        if request.form['destination']:
            editFlight.destination = request.form['destination']
        if request.form['time']:
            editFlight.time = request.form['time']
        if request.form['fare']:
            editFlight.fare = request.form['fare']
        session.add(editFlight)
        session.commit()
        flash('Flight Info Edited Successfully')
        return redirect(url_for('showFlightInfo',
                                flightpartner_id=flightpartner_id))
    else:
        return render_template('editFlight.html',
                               flightpartner_id=flightpartner_id,
                               info_id=info_id, flight=editFlight)

# Flight Information Delete


@app.route('/flightpartner/<int:flightpartner_id>/info/<int:info_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteFlight(flightpartner_id, info_id):
    flightpartner = session.query(FlightPartner).filter_by(
                                  id=flightpartner_id).one()
    flightToDelete = session.query(FlightInfo).filter_by(id=info_id).one()
    if login_session['user_id'] != flightpartner.user_id:
        return "<script>function myFunction()"
        "{alert('You are not authorized to delete flights of this"
        "flightpartner. Please create your own"
        "flightpartner in order to"
        "delete flights.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(flightToDelete)
        session.commit()
        flash('Flight Info Deleted Successfully')
        return redirect(url_for('showFlightInfo',
                                flightpartner_id=flightpartner_id))
    else:
        return render_template('deleteFlight.html',
                               flightpartner_id=flightpartner_id,
                               flight=flightToDelete)

# User Disconnect


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            login_session.clear()
            flash("You have successfully been logged out.")
            return redirect(url_for('showFlightPartners'))
        else:
            flash("You were not logged in")
            return redirect(url_for('showFlightPartners'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
