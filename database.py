from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

load_dotenv()

URL_DATABASE = os.getenv('URL_DATABASE')
engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autoflush=False , autocommit = False , bind=engine)
Base = declarative_base()
Base.metadata.create_all(bind=engine)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
