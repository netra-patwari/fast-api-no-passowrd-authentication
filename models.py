from sqlalchemy import Boolean, Column , Integer , String , Text
from database import Base

class User(Base):
    __tablename__='user'
    
    id = Column(Integer , primary_key=True , index=True)
    first_name = Column(String)
    last_name = Column(String)
    profile_photo = Column(Text)
    email = Column(String)
    country_code = Column(String)
    phone_no = Column(String)
    access_token = Column(String)
    verified_at = Column(String) 
    user_validation_id = Column(String)  
    is_verified = Column(Boolean , default=False)
    is_registered = Column(Boolean , default=False)
    




class OTP(Base):
    __tablename__='otp'
    
    id = Column(Integer , primary_key=True , index=True)
    otp = Column(String,index=True)
    user_id = Column(Integer)
    otp_generated_datetime = Column(String)
    otp_expiration_time = Column(String)
