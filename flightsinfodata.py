from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, FlightPartner, FlightInfo, User

engine = create_engine('sqlite:///flightsinfo.db')
"""Bind the engine to the metadata of the Base class so that the
declaratives can be accessed through a DBSession instance"""
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
"""A DBSession() instance establishes all conversations with the database
 and represents a "staging zone" for all the objects loaded into the
 database session object. Any change made against the objects in the
 session won't be persisted into the database until you call
 session.commit(). If you're not happy about the changes, you can
 revert all of them back to the last commit by calling
 session.rollback()"""
session = DBSession()


"""Create user"""
User1 = User(name="Bhavani", email="durgabhavani.vankini@gmail.com",
             picture='https://lh6.googleusercontent.com'
             '/-ODf1V0QoS2Q/AAAAAAAAAAI/AAAAAAAAAAA/'
             'saglyR2exWU/W96-H96/photo.jpg')
session.add(User1)
session.commit()

# Air India Flights
flightpartner1 = FlightPartner(user_id=1, name="AirIndia",
                               logo="https://tinyurl.com/y2vapn6g")
session.add(flightpartner1)
session.commit()

flightsinfo = FlightInfo(user_id=1, source="Hyderabad",
                         destination="New Delhi",
                         fare="$120",
                         time="9 AM",
                         flight_partner=flightpartner1)
session.add(flightsinfo)
session.commit()

flightsinfo = FlightInfo(user_id=1, source="Kochi",
                         destination="Chennai",
                         fare="$50",
                         time="11 AM",
                         flight_partner=flightpartner1)
session.add(flightsinfo)
session.commit()


# IndiGo Flights
flightpartner2 = FlightPartner(user_id=1, name="IndiGo",
                               logo="https://tinyurl.com/yybwdgau")
session.add(flightpartner2)
session.commit()

flightsinfo = FlightInfo(user_id=1, source="Banglore",
                         destination="Noida",
                         fare="$20",
                         time="3 PM",
                         flight_partner=flightpartner2)
session.add(flightsinfo)
session.commit()

flightsinfo = FlightInfo(user_id=1, source="New Delhi",
                         destination="Australia",
                         fare="$60",
                         time="11 AM",
                         flight_partner=flightpartner2)
session.add(flightsinfo)
session.commit()

# SpiceJet Flights
flightpartner3 = FlightPartner(user_id=1, name="SpiceJet",
                               logo="https://tinyurl.com/y699fxdt")
session.add(flightpartner3)
session.commit()

flightsinfo = FlightInfo(user_id=1, source="Europe",
                         destination="Noida",
                         fare="$120",
                         time="5 PM",
                         flight_partner=flightpartner3)
session.add(flightsinfo)
session.commit()

flightsinfo = FlightInfo(user_id=1, source="Banglore",
                         destination="Hyderabad",
                         fare="$60",
                         time="10 AM",
                         flight_partner=flightpartner3)
session.add(flightsinfo)
session.commit()

# Jet Airways Flights
flightpartner4 = FlightPartner(user_id=1, name="Jet Airways",
                               logo="https://tinyurl.com/y54oryaa")
session.add(flightpartner4)
session.commit()

flightsinfo = FlightInfo(user_id=1, source="Chennai",
                         destination="Hyderabad",
                         fare="$20",
                         time="4 PM",
                         flight_partner=flightpartner4)
session.add(flightsinfo)
session.commit()

flightsinfo = FlightInfo(user_id=1, source="New Delhi",
                         destination="Australia",
                         fare="$50",
                         time="12 PM",
                         flight_partner=flightpartner4)
session.add(flightsinfo)
session.commit()

print("added menu items!")
