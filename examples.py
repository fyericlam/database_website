from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Catalog, Item

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()


"""Create new table entry to database"""

# Initial user
user1 = User(name='FY Eric Lam',
             email='brick.ericlam@gmail.com')
session.add(user1)
session.commit()

# Catalog -- Tasty Burgundy
catalog1 = Catalog(name="Tasty Burgundy",
                   user=user1)
session.add(catalog1)
session.commit()

item1 = Item(name="2005 Domaine Ponsot Clos de la Roche Grand Cru 'Cuvee Vieilles Vignes'",
             vintage='2005',
             price='$9,447',
             score='95/100',
             producer='Domaine Ponsot',
             region='Clos de la Roche, Morey-Saint-Denis, Cote de Nuits, Burgundy, France',
             grape='Pinot Noir',
             food='Duck, Goose and Game Birds',
             style='Red - Savory and Classic',
             catalog=catalog1,
             user=user1)
session.add(item1)
session.commit()


item2 = Item(name="2009 Leroy Domaine d'Auvenay Meursault",
             vintage='2009',
             price='$9,198',
             score='N/A',
             producer="Domaine d'Auvenay",
             region='Meursault, Cote de Beaune, Burgundy, France',
             grape='Chardonnay',
             food='Chicken and Turkey',
             style='White - Buttery and Complex',
             catalog=catalog1,
             user=user1)
session.add(item2)
session.commit()

# Catalog -- Happy Champagne
catalog2 = Catalog(name="Happy Champagne",
                   user=user1)
session.add(catalog2)
session.commit()

item1 = Item(name='Jacques Selosse Substance Grand Cru Blanc de Blancs Brut',
             vintage='N/A',
             price='$2,531',
             score='93/100',
             producer='Jacques Selosse Estate',
             region='Champagne Blanc de Blancs, Champagne, France',
             grape='Chardonnay',
             food='Shellfish, Crab and Lobster',
             style='Sparkling - Complex and Traditional',
             catalog=catalog2,
             user=user1)
session.add(item1)
session.commit()

item2 = Item(name='2004 Krug Brut',
             vintage='2004',
             price='$2,136',
             score='90/100',
             producer='Krug',
             region='Champagne, France',
             grape='Champagne Blend',
             food='Shellfish, Crab and Lobster',
             style='Sparkling - Complex and Traditional',
             catalog=catalog2,
             user=user1)
session.add(item2)
session.commit()

print("Added catalogs and/or items!")
