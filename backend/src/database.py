from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,Session

Base = declarative_base()
engine = create_engine("sqlite:///news_database.db", echo=True)

Base.metadata.create_all(engine)
Session_global=sessionmaker(bind=engine)

def session_opener():
    session = Session(bind=engine)
    try:
        yield session
    finally:
        session.close()
