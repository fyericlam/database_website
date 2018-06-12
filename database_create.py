from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Shop, CatalogItem

engine = create_engine('sqlite:///shopCatalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


"""Create new table entry to database"""

# Catalog for Tasty Burgundy
shop1 = Shop(name="Tasty Burgundy")
session.add(shop1)
session.commit()

catalogItem1 = CatalogItem(name="2005 Domaine Ponsot Clos de la Roche Grand Cru 'Cuvee Vieilles Vignes'",
                           vintage='2005',
                           price='$9447',
                           score='95',
                           producer='Domaine Ponsot',
                           region='Clos de la Roche, Morey-Saint-Denis, Cote de Nuits, Burgundy, France',
                           grape='Pinot Noir',
                           food='Duck, Goose and Game Birds',
                           style='Red - Savory and Classic',
                           shop=shop1)
session.add(catalogItem1)
session.commit()

# Catalog for Happy Champagne
shop2 = Shop(name="Happy Champagne")
session.add(shop2)
session.commit()

catalogItem2 = CatalogItem(name='2004 Krug Brut',
                           vintage='2004',
                           price='$2136',
                           score='90',
                           producer='Krug',
                           region='Champagne, France',
                           grape='Champagne Blend',
                           food='Shellfish, Crab and Lobster',
                           style='Sparkling - Complex and Traditional',
                           shop=shop2)
session.add(catalogItem2)
session.commit()

print("Added shops and/or catalog items!")
