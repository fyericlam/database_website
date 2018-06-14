from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Shop, CatalogItem

engine = create_engine('sqlite:///shopCatalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


"""Create new table entry to database"""

# Initial user
user1 = User(name='Great Gatsby',
             email='great@gatsby.com')
session.add(user1)
session.commit()

user2 = User(name='Small Potato',
             email='small@potato.com')
session.add(user2)
session.commit()

# Catalog for Tasty Burgundy
shop1 = Shop(name="Tasty Burgundy",
             user=user1)
session.add(shop1)
session.commit()

catalogItem1 = CatalogItem(name="2005 Domaine Ponsot Clos de la Roche Grand Cru 'Cuvee Vieilles Vignes'",
                           vintage='2005',
                           price='$9,447',
                           score='95/100',
                           producer='Domaine Ponsot',
                           region='Clos de la Roche, Morey-Saint-Denis, Cote de Nuits, Burgundy, France',
                           grape='Pinot Noir',
                           food='Duck, Goose and Game Birds',
                           style='Red - Savory and Classic',
                           shop=shop1,
                           user=user1)
session.add(catalogItem1)
session.commit()

# Catalog for Happy Champagne
shop2 = Shop(name="Happy Champagne",
             user=user2)
session.add(shop2)
session.commit()

catalogItem2 = CatalogItem(name='2004 Krug Brut',
                           vintage='2004',
                           price='$2,136',
                           score='90/100',
                           producer='Krug',
                           region='Champagne, France',
                           grape='Champagne Blend',
                           food='Shellfish, Crab and Lobster',
                           style='Sparkling - Complex and Traditional',
                           shop=shop2,
                           user=user2)
session.add(catalogItem2)
session.commit()

print("Added shops and/or catalog items!")
