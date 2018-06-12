from flask import Flask

app = Flask(__name__)


@app.route('/')
@app.route('/shops/')
def showShops():
    return 'This page shows all my shops'


@app.route('/shops/new/')
def newShop():
    return 'This page makes new shop'


@app.route('/shops/<int:shop_id>/edit/')
def editShop(shop_id):
    return 'This page edits shop {}'.format(shop_id)


@app.route('/shops/<int:shop_id>/delete/')
def deleteShop(shop_id):
    return 'This page deletes shop {}'.format(shop_id)


@app.route('/shops/<int:shop_id>/')
@app.route('/shops/<int:shop_id>/catalog/')
def showCatalog(shop_id):
    return 'This page displays catalog for shop {}'.format(shop_id)


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
