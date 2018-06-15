from flask import Flask, render_template, request, redirect, url_for, jsonify,\
    flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Catalog, Item

from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Retrieve client info
CLIENT_ID = \
    json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


@app.route('/login')
def showLogin():
    '''Create anti-forgery state token'''
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Sign-in helper functions
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
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


# Google+ sign in
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Turn authorization code into credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={}'
           .format(access_token))
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # Abort if error was in the access token info
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify access token is used for intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify access token is valid for app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user already connected'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store access token in session for later use
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # Add provider to login session
    login_session['provider'] = 'google'

    # See if user exists, make a new one if it doesn't
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style="width: 300px; height: 300px;'
    output += ' border-radius: 150px; -webkit-border-radius: 150px;'
    output += ' -moz-border-radius: 150px;">'
    flash('Now logged in as {}'.format(login_session['username']))
    print('Done!')
    return output


# Google+ sign out
@app.route('/gdisconnect/')
def gdisconnect():
    # Only disconnect connected user
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token={}'.format(
        access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# Facebook sign in
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print("Access token received {}".format(access_token))

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = 'https://graph.facebook.com/v2.8/me'
    ''' Due to the formatting for result from server token exchange need to
        split token first on commas and select first index which gives the
        key : value for server access token then we split it on colons to pull
        out actual token value and replace remaining quotes with nothing so
        it can be used directly in graph api calls
    '''
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['email'] = data['email']
    login_session['facebook_id'] = data['id']

    # Token must be stored in login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data['data']['url']

    # see if user exists
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
    output += ' " style="width: 300px; height: 300px;'
    output += ' border-radius: 150px; -webkit-border-radius: 150px;'
    output += ' -moz-border-radius: 150px;">'
    flash('Now logged in as {}'.format(login_session['username']))
    print('Done!')
    return output


# Facebook sign out
@app.route('/fbdisconnect/')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # Access token must be included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token={}'.format(
        facebook_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "Successfully logged out"


@app.route('/disconnect')
def disconnect():
    '''Disconnect based on provider'''
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("Successfully logged out")
        return redirect(url_for('showCatalogs'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCatalogs'))


@app.route('/')
@app.route('/catalogs/')
def showCatalogs():
    """This page shows all the catalogs"""
    catalogs = session.query(Catalog).order_by(Catalog.name).all()
    if 'username' not in login_session:
        return render_template('showCatalogs.html', catalogs=catalogs)
    else:
        return render_template('showCatalogs_private.html', catalogs=catalogs)


@app.route('/catalogs/JSON/')
def showCatalogs_JSON():
    """This page shows all the catalogs in JSON"""
    catalogs = session.query(Catalog).all()
    cols = ['name']
    results = [{col: getattr(catalog, col) for col in cols}
               for catalog in catalogs]
    return jsonify(Catalogs=results)


@app.route('/catalogs/new/', methods=['GET', 'POST'])
def newCatalog():
    """This page makes new catalog"""
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCatalog = Catalog(name=request.form['name'],
                             user_id=login_session['user_id'])
        session.add(newCatalog)
        session.commit()
        flash('New catalog sucessfully created!')
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newCatalog.html')


@app.route('/catalogs/<int:catalog_id>/edit/', methods=['GET', 'POST'])
def editCatalog(catalog_id):
    """This page edits catalog <catalog_id>"""
    if 'username' not in login_session:
        return redirect('/login')
    editCatalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if editCatalog.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('Only owner is authorized to edit catalog.');} window.location='/catalogs/';</script><body onload='myFunction()'>"
    if request.method == 'POST':
        editCatalog.name = request.form['name']
        session.add(editCatalog)
        session.commit()
        flash('Catalog sucessfully edited!')
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('editCatalog.html',
                               editCatalog=editCatalog)


@app.route('/catalogs/<int:catalog_id>/delete/', methods=['GET', 'POST'])
def deleteCatalog(catalog_id):
    """This page deletes catalog <catalog_id>"""
    if 'username' not in login_session:
        return redirect('/login')
    deleteCatalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if deleteCatalog.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('Only owner is authorized to delete catalog.');} window.location='/catalogs/';</script><body onload='myFunction()'>"
    if request.method == 'POST':
        session.delete(deleteCatalog)
        session.commit()
        flash('Catalog sucessfully deleted!')
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('deleteCatalog.html',
                               deleteCatalog=deleteCatalog)


@app.route('/catalogs/<int:catalog_id>/')
@app.route('/catalogs/<int:catalog_id>/items/')
def showItems(catalog_id):
    """This page displays items for catalog <catalog_id>"""
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    owner = session.query(User).filter_by(id=catalog.user_id).one()
    items = session.query(Item).filter_by(catalog_id=catalog_id).all()
    if 'username' not in login_session or owner.id != login_session['user_id']:
        return render_template('showItems.html',
                               catalog=catalog,
                               owner=owner,
                               items=items)
    else:
        return render_template('showItems_private.html',
                               catalog=catalog,
                               owner=owner,
                               items=items)


@app.route('/catalogs/<int:catalog_id>/items/JSON/')
def showItems_JSON(catalog_id):
    """This page displays items for catalog <catalog_id> in JSON"""
    items = session.query(Item).filter_by(catalog_id=catalog_id).all()
    cols = ['name', 'vintage', 'price', 'score',
            'producer', 'region', 'grape', 'food', 'style']
    results = [{col: getattr(item, col) for col in cols} for item in items]
    return jsonify(Items=results)


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>/JSON/')
def showItem_JSON(catalog_id, item_id):
    """This page displays item <item_id> for catalog <catalog_id> in JSON"""
    item = session.query(Item).filter_by(
        catalog_id=catalog_id, id=item_id).one()
    cols = ['name', 'vintage', 'price', 'score',
            'producer', 'region', 'grape', 'food', 'style']
    result = {col: getattr(item, col) for col in cols}
    return jsonify(Item=result)


@app.route('/catalogs/<int:catalog_id>/items/new/', methods=['GET', 'POST'])
def newItem(catalog_id):
    """This page makes new item for catalog <catalog_id>"""
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if catalog.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('Only owner is authorized to create item.'); window.location='/catalogs/';}</script><body onload='myFunction()'>"
    if request.method == 'POST':
        newItem = Item(name=request.form['name'],
                       vintage=request.form['vintage'],
                       price=request.form['price'],
                       score=request.form['score'],
                       producer=request.form['producer'],
                       region=request.form['region'],
                       grape=request.form['grape'],
                       food=request.form['food'],
                       style=request.form['style'],
                       catalog_id=catalog_id)
        session.add(newItem)
        session.commit()
        flash('Item sucessfully created!')
        return redirect(url_for('showItems', catalog_id=catalog_id))
    else:
        return render_template('newItem.html', catalog=catalog)


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>/edit/',
           methods=['GET', 'POST'])
def editItem(catalog_id, item_id):
    """This page edits item <item_id> in catalog <catalog_id>"""
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if catalog.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('Only owner is authorized to edit item.'); window.location='/catalogs/';}</script><body onload='myFunction()'>"
    editItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editItem.name = request.form['name']
        if request.form['vintage']:
            editItem.vintage = request.form['vintage']
        if request.form['price']:
            editItem.price = request.form['price']
        if request.form['score']:
            editItem.score = request.form['score']
        if request.form['producer']:
            editItem.producer = request.form['producer']
        if request.form['region']:
            editItem.region = request.form['region']
        if request.form['grape']:
            editItem.grape = request.form['grape']
        if request.form['food']:
            editItem.food = request.form['food']
        if request.form['style']:
            editItem.style = request.form['style']
        session.add(editItem)
        session.commit()
        flash('Item sucessfully edited!')
        return redirect(url_for('showItems', catalog_id=catalog_id))
    else:
        return render_template('editItem.html',
                               catalog=catalog,
                               editItem=editItem)


@app.route('/catalogs/<int:catalog_id>/items/<int:item_id>/delete/',
           methods=['GET', 'POST'])
def deleteItem(catalog_id, item_id):
    """This page deletes item <item_id> in catalog <catalog_id>"""
    if 'username' not in login_session:
        return redirect('/login')
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    if catalog.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('Only owner is authorized to delete item.'); window.location='/catalogs/';}</script><body onload='myFunction()'>"
    deleteItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(deleteItem)
        session.commit()
        flash('Item sucessfully deleted!')
        return redirect(url_for('showItems', catalog_id=catalog_id))
    else:
        return render_template('deleteItem.html',
                               catalog=catalog,
                               deleteItem=deleteItem)


if __name__ == '__main__':
    app.secret_key = 'ericlam'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
