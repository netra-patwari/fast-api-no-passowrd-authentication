from fastapi import APIRouter , Depends , Header ,HTTPException
from fastapi.responses import JSONResponse
import re
import random
from datetime import datetime , timedelta
from models import User , OTP
from pydantic import BaseModel , EmailStr , validator
from database import SessionLocal
from sqlalchemy.orm import Session
import secrets
from database import get_db
import smtplib
from email.message import EmailMessage

router = APIRouter(
    prefix='/auth'
)


email_address = "patwarinetra@gmail.com" 
email_password = "wriq lzar tcas hgih" 

msg = EmailMessage()

        

def success_response(data):
    return {"data": data, "meta": {"status": 200, "message": "Success"}}

class User_info(BaseModel):
    first_name: str
    last_name: str
    profile_photo: str
    country_code : str
    phone_no : str
    email : str
    
    @validator("phone_no")
    def validate_phone_no(cls, v):
        if not isinstance(v, str):
            raise ValueError("Phone number must be a string")
        if not v.isdigit():
            raise ValueError("Phone number must contain only digits")
        if len(v) != 10:
            raise ValueError("Phone number must be 10 digits long")
        return v





@router.post('/create-user') 
async def create_user(email:EmailStr, db: Session = Depends(get_db)): 
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if re.fullmatch(regex, email):
        user_email_in_db = db.query(User).filter(User.email == email).first()
        if user_email_in_db is None:
            user_validation_id = secrets.token_hex(32)
            access_token = secrets.token_urlsafe(64)
            db_email = User(email=email , user_validation_id=user_validation_id , access_token=access_token)
            
            db.add(db_email)
            db.commit()
            db.refresh(db_email)
            user = db.query(User).filter(User.email == email).first()

            otp = random.randint(1000,9999)
            otp_generated_datetime = datetime.now()
            otp_expiration_time = otp_generated_datetime + timedelta(minutes=2)
            user_id = user.id
            
            db_otp = OTP(otp=otp , otp_generated_datetime=otp_generated_datetime , otp_expiration_time=otp_expiration_time , user_id=user_id)
            db.add(db_otp)
            db.commit()
            db.refresh(db_otp)
            
            msg['Subject'] = f'{otp} is your verification code'
            msg['From'] = email_address
            msg['To'] = email 
            msg.set_content(
            f"""\
                Testing 
            """,
                
            )
            # send email
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(email_address, email_password)
                smtp.send_message(msg)
            
            data ={'user_validation_id' : user_validation_id}
            return success_response(data)
        
        else:

            raise HTTPException(status_code=400 , detail='User already exists')

    else:
        raise HTTPException(status_code=400 , detail='Invalid Email')

        

@router.post('/validate_otp')
async def validate_otp( otp: str , user_validation_id: str , db: Session = Depends(get_db)) : 
    user = db.query(User).filter(User.user_validation_id == user_validation_id).first()
    if user :
        db_otp = db.query(OTP).filter(OTP.user_id == user.id).first()
        if db_otp:
            datetime_object = datetime.strptime(db_otp.otp_expiration_time, "%Y-%m-%d %H:%M:%S.%f")
            if  db_otp.otp == otp and datetime_object >= datetime.now():
                verified_at = datetime.now()
                user.is_verified = True
                user.verified_at = verified_at
                
                db.commit()
                access_token = user.access_token
                is_registered=user.is_registered
                data = {
                    'access_token' : access_token,
                    'is_registered' : is_registered
                }
                return success_response(data) 
            
            elif datetime_object < datetime.now(): 
                raise HTTPException(status_code=400 , detail='Your OTP has expired.')
            else:
                raise HTTPException(status_code=400 , detail='Invalid OTP')
 


@router.post('/resend_otp')
async def resend_otp(user_validation_id: str, db: Session = Depends(get_db)) : 
    user = db.query(User).filter(User.user_validation_id == user_validation_id).first()
    if user:
        db_otp = db.query(OTP).filter(OTP.user_id == user.id).first()
        new_otp = random.randint(1000,9999)
        otp_generated_datetime = datetime.now()
        otp_expiration_time = otp_generated_datetime + timedelta(minutes=2)
        
        
        db_otp.otp = new_otp
        db_otp.otp_generated_datetime = otp_generated_datetime
        db_otp.otp_expiration_time = otp_expiration_time
        db.commit()
        
        msg['Subject'] = f'{new_otp} is your verification code'
        msg['From'] = email_address
        msg['To'] = user.email 
        msg.set_content(
        f"""\
            Testing 
        """,
            
        )
        # send email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
    
        data ={'user_validation_id' : user_validation_id}
        return success_response(data)
    else:
        raise HTTPException(status_code=400 , detail='Invalid email')
 
   

@router.post('/register')
async def register( user_info : User_info , access_token: str = Header(None) ,  db: Session = Depends(get_db)) : 
    user = db.query(User).filter(User.access_token == access_token).first()
    
    if user and user.email ==  user_info.email and user.is_registered == False:
        
        
        
        if len(user_info.profile_photo.encode('utf-8')) <= 2 * 1024 * 1024:
            user.first_name = user_info.first_name
            user.last_name = user_info.last_name

            user.profile_photo = user_info.profile_photo
            user.country_code = user_info.country_code
            user.phone_no = user_info.phone_no
            
            
            user.access_token = secrets.token_urlsafe(64)
            user.is_registered = True
            
            db.commit()
            data = {access_token : 'access_token' }
            return success_response(data)
    else:
        raise HTTPException(status_code=404, detail="User not found or already registered")






@router.post("/login")
async def login(email: EmailStr, db: Session = Depends(get_db) )  :
    
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if re.fullmatch(regex, email):
            print("Valid Email")
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                print('User not in db')
                data = { 'user_validation_id' : user_validation_id }
                return success_response(data)
            
            
            elif user:

                otp = random.randint(1000,9999)
                otp_generated_datetime = datetime.now()
                otp_expiration_time = otp_generated_datetime + timedelta(minutes=2)
                
                
                user_id = user.id
                user_validation_id = user.user_validation_id 
                
                
                db_otp = db.query(OTP).filter(OTP.user_id == user_id).first()
                db_otp.otp=  otp 
                db_otp.otp_generated_datetime=otp_generated_datetime 
                db_otp.otp_expiration_time=otp_expiration_time 
                db.commit()
                db.refresh(db_otp)
                
                msg['Subject'] = f'{otp} is your verification code'
                msg['From'] = email_address
                msg['To'] = email 
                msg.set_content(
                f"""\
                  Testing 
                """,
                    
                )
                # send email
                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                    smtp.login(email_address, email_password)
                    smtp.send_message(msg)
 
            data ={'user_validation_id' : user_validation_id}
            return success_response(data)
            # return login_is_user(user_validation_id)
        
    else:
        raise HTTPException(status_code=404, detail="Invalid Email ID")
    
    
