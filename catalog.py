from flask import Flask, render_template, request, redirect, url_for

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Shop, CatalogItem

app = Flask(__name__)

engine = create_engine('sqlite:///shopCatalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/')
@app.route('/shops/')
def showShops():
    """This page shows all my shops"""
    shops = session.query(Shop).all()
    return render_template('showShops.html', shops=shops)


@app.route('/shops/new/', methods=['GET', 'POST'])
def newShop():
    """This page makes new shop"""
    if request.method == 'POST':
        newShop = Shop(name=request.form['name'])
        session.add(newShop)
        session.commit()
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
    showCatalog = session.query(CatalogItem).filter_by(
        shop_id=shop_id).all()
    return render_template('showCatalog.html',
                           shop=shop,
                           showCatalog=showCatalog)


@app.route('/shops/<int:shop_id>/catalog/new/')
def newCatalogItem(shop_id):
    return 'This page makes new catalog item for shop {}'.format(
        shop_id)


@app.route('/shops/<int:shop_id>/catalog/<int:catalog_id>/edit/')
def editCatalogItem(shop_id, catalog_id):
    return 'This page edits catalog item {}'.format(catalog_id)


@app.route('/shops/<int:shop_id>/catalog/<int:catalog_id>/delete/')
def deleteCatalogItem(shop_id, catalog_id):
    return 'This page deletes catalog item {}'.format(catalog_id)


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
