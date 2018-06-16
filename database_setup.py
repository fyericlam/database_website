# Configuration (beginning)
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    # Table information
    __tablename__ = 'user'
    # Mappers
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    email = Column(String(80), nullable=False)
    picture = Column(String(80))


class Catalog(Base):
    # Table information
    __tablename__ = 'catalog'
    # Mappers
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


class Item(Base):
    # Table information
    __tablename__ = 'item'
    # Mappers
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    vintage = Column(String(4), nullable=False)
    price = Column(String(10), nullable=False)
    score = Column(String(3))
    producer = Column(String(50))
    region = Column(String(250))
    grape = Column(String(50))
    food = Column(String(100), nullable=False)
    style = Column(String(100))
    catalog_id = Column(Integer, ForeignKey('catalog.id'))
    catalog = relationship(Catalog, backref=backref(
        'items', cascade='all, delete-orphan'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


# Configuration (ending)
engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
