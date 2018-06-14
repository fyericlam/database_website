from flask import Flask, render_template, request, redirect, url_for, jsonify,\
    flash

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Shop, CatalogItem

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
engine = create_engine('sqlite:///shopCatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Retrieve client info
CLIENT_ID = \
    json.loads(open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


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
    flash('You are now logged in as {}'.format(login_session['username']))
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
        return redirect(url_for('showShops'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showShops'))


@app.route('/')
@app.route('/shops/')
def showShops():
    """This page shows all the shops"""
    shops = session.query(Shop).order_by(Shop.name).all()
    if 'username' not in login_session:
        return render_template('showShops.html', shops=shops)
    else:
        return render_template('showShops_private.html', shops=shops)


@app.route('/shops/JSON/')
def showShops_JSON():
    """This page shows all my shops in JSON"""
    shops = session.query(Shop).all()
    cols = ['name']
    results = [{col: getattr(shop, col) for col in cols} for shop in shops]
    return jsonify(Shops=results)


@app.route('/shops/new/', methods=['GET', 'POST'])
def newShop():
    """This page makes new shop"""
    if request.method == 'POST':
        newShop = Shop(name=request.form['name'])
        session.add(newShop)
        session.commit()
        flash('New shop sucessfully created!')
        return redirect(url_for('showShops'))
    else:
        return render_template('newShop.html')


@app.route('/shops/<int:shop_id>/edit/', methods=['GET', 'POST'])
def editShop(shop_id):
    """This page edits shop <shop_id>"""
    editShop = session.query(Shop).filter_by(
        id=shop_id).one()
    if request.method == 'POST':
        editShop.name = request.form['name']
        session.add(editShop)
        session.commit()
        flash('Shop sucessfully edited!')
        return redirect(url_for('showShops'))
    else:
        return render_template('editshop.html',
                               editShop=editShop)


@app.route('/shops/<int:shop_id>/delete/', methods=['GET', 'POST'])
def deleteShop(shop_id):
    """This page deletes shop <shop_id>"""
    deleteShop = session.query(Shop).filter_by(
        id=shop_id).one()
    if request.method == 'POST':
        session.delete(deleteShop)
        session.commit()
        flash('Shop sucessfully deleted!')
        return redirect(url_for('showShops'))
    else:
        return render_template('deleteShop.html',
                               deleteShop=deleteShop)


@app.route('/shops/<int:shop_id>/')
@app.route('/shops/<int:shop_id>/catalog/')
def showCatalog(shop_id):
    """This page displays catalog for shop <shop_id>"""
    shop = session.query(Shop).filter_by(
        id=shop_id).one()
    user = session.query(User).filter_by(
        id=shop.user_id).one()
    showCatalog = session.query(CatalogItem).filter_by(
        shop_id=shop_id).all()
    return render_template('showCatalog.html',
                           shop=shop,
                           user=user,
                           showCatalog=showCatalog)


@app.route('/shops/<int:shop_id>/catalog/JSON/')
def showCatalog_JSON(shop_id):
    """This page displays catalog for shop <shop_id> in JSON"""
    showCatalog = session.query(CatalogItem).filter_by(
        shop_id=shop_id).all()
    cols = ['name', 'vintage', 'price', 'score',
            'producer', 'region', 'grape', 'food', 'style']
    results = [{col: getattr(item, col) for col in cols}
               for item in showCatalog]
    return jsonify(Catalog=results)


@app.route('/shops/<int:shop_id>/catalog/<int:catalog_id>/JSON/')
def showCatalogItem_JSON(shop_id, catalog_id):
    """This page displays catalog item <catalog_id> for shop <shop_id> in JSON
    """
    showCatalogItem = session.query(CatalogItem).filter_by(
        shop_id=shop_id, id=catalog_id).one()
    cols = ['name', 'vintage', 'price', 'score',
            'producer', 'region', 'grape', 'food', 'style']
    result = {col: getattr(showCatalogItem, col) for col in cols}
    return jsonify(Catalog=result)


@app.route('/shops/<int:shop_id>/catalog/new/', methods=['GET', 'POST'])
def newCatalogItem(shop_id):
    """This page makes new catalog item for shop <shop_id>"""
    shop = session.query(Shop).filter_by(id=shop_id).one()
    if request.method == 'POST':
        newCatalogItem = CatalogItem(name=request.form['name'],
                                     vintage=request.form['vintage'],
                                     price=request.form['price'],
                                     shop_id=shop_id)
        session.add(newCatalogItem)
        session.commit()
        flash('Catalog item sucessfully created!')
        return redirect(url_for('showCatalog', shop_id=shop_id))
    else:
        return render_template('newCatalogItem.html', shop=shop)


@app.route('/shops/<int:shop_id>/catalog/<int:catalog_id>/edit/',
           methods=['GET', 'POST'])
def editCatalogItem(shop_id, catalog_id):
    """This page edits catalog item <catalog_id>"""
    shop = session.query(Shop).filter_by(id=shop_id).one()
    editCatalogItem = session.query(CatalogItem).filter_by(id=catalog_id).one()
    if request.method == 'POST':
        editCatalogItem.name = request.form['name']
        editCatalogItem.vintage = request.form['vintage']
        editCatalogItem.price = request.form['price']
        session.add(editCatalogItem)
        session.commit()
        flash('Catalog item sucessfully edited!')
        return redirect(url_for('showCatalog', shop_id=shop_id))
    else:
        return render_template('editCatalogItem.html',
                               shop=shop,
                               editCatalogItem=editCatalogItem)


@app.route('/shops/<int:shop_id>/catalog/<int:catalog_id>/delete/',
           methods=['GET', 'POST'])
def deleteCatalogItem(shop_id, catalog_id):
    """This page deletes catalog item <catalog_id>"""
    shop = session.query(Shop).filter_by(id=shop_id).one()
    deleteCatalogItem = session.query(
        CatalogItem).filter_by(id=catalog_id).one()
    if request.method == 'POST':
        session.delete(deleteCatalogItem)
        session.commit()
        flash('Catalog item sucessfully deleted!')
        return redirect(url_for('showCatalog', shop_id=shop_id))
    else:
        return render_template('deleteCatalogItem.html',
                               shop=shop,
                               deleteCatalogItem=deleteCatalogItem)


if __name__ == '__main__':
    app.secret_key = 'ericlam'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
