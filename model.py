from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, BIGINT, BLOB, VARCHAR, Text, Binary, LargeBinary, DateTime
from sqlalchemy.orm import deferred
from sqlalchemy.orm import defer, undefer

engine = create_engine('mysql+pymysql://root:P1@192.168.100.181/presenca', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
session = Session()

class Participantes(Base):
    __tablename__ = 'participantes'

    id = Column(BIGINT, primary_key=True)
    participant_name = Column(VARCHAR(100))
    phone = Column(VARCHAR(20))
    email = Column(VARCHAR(50))
    domain = Column(VARCHAR(50))


class Presenca(Base):
    __tablename__ = 'presenca'

    id = Column(BIGINT, primary_key=True)
    client_name = Column(String(500), nullable=False, unique=True)
    date_checkin = Column(DateTime)
    
    def __repr__(self):
        return 'hostname %s' % (self.client_name)


class Imagesdata(Base):
    __tablename__ = 'images'
    
    id = Column(BIGINT, primary_key=True)
    client_name = Column(String(500), nullable=False)    
    photo = Column(LargeBinary)

    def __repr__(self):
        return 'hostname %s' % (self.client_name)