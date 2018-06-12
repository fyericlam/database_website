# Configuration (beginning)
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# Class definitions


class Shop(Base):
    # Table information
    __tablename__ = 'shop'
    # Mappers
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)


class CatalogItem(Base):
    # Table information
    __tablename__ = 'catalog_item'
    # Mappers
    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    vintage = Column(String(4), nullable=False)
    price = Column(String(250), nullable=False)
    score = Column(String(3))
    producer = Column(String(50))
    region = Column(String(250))
    grape = Column(String(50))
    food = Column(String(100))
    style = Column(String(100))
    shop_id = Column(Integer, ForeignKey('shop.id'))
    shop = relationship(Shop)


# Configuration (ending)
engine = create_engine('sqlite:///shopCatalog.db')

Base.metadata.create_all(engine)
