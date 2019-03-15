from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class FlightPartner(Base):
    __tablename__ = 'flightpartner'
    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    logo = Column(String(250))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


@property
def serialize(self):
    """Return object data in easily serializeable format"""
    return {'name': self.name, 'id': self.id}


class FlightInfo(Base):
    __tablename__ = 'flightinfo'
    source = Column(String(80), nullable=False)
    destination = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    time = Column(String(250))
    fare = Column(String(8))
    flight_id = Column(Integer, ForeignKey('flightpartner.id'))
    flight_partner = relationship(FlightPartner, backref=backref(
        'flightinfo', cascade='all,delete'))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)


@property
def serialize(self):
    """Return object data in easily serializeable format"""
    return {'source': self.source,
            'destination': self.destination,
            'id': self.id,
            'time': self.time,
            'fare': self.fare}


engine = create_engine('sqlite:///flightsinfo.db')
Base.metadata.create_all(engine)
