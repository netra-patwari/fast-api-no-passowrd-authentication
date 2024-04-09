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
from dotenv import load_dotenv
import os


load_dotenv()

router = APIRouter(
    prefix='/auth'
)


email_address = os.getenv('EMAIL_ADD')
email_password = os.getenv('EMAIL_PASS') 
msg = EmailMessage()

        

def success_response(data):
    return {"data": data, "meta": {"status": 200, "message": "Success"}}

def error_response(status_code , detail):
    return { 'data' : {} , 'meta' :  { 'status' : status_code , 'message' :detail  }  }

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


class Email(BaseModel):
    email: EmailStr

class ValidateOtp(BaseModel):
    otp: str
    user_validation_id : str


class Us(BaseModel):
    user_validation_id : str

async def send_email(email, otp):
    try:
        msg = EmailMessage()
        msg['Subject'] = f'{otp} is your verification code'
        msg['From'] = email_address
        msg['To'] = email
        msg.set_content("Testing")

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error sending email: {e}")
        return error_response(status_code=500, detail="Error sending email")
    

async def handle_login(email, db: Session):
    otp = random.randint(1000, 9999)
    otp_generated_datetime = datetime.now()
    otp_expiration_time = otp_generated_datetime + timedelta(minutes=2)

    user = db.query(User).filter(User.email == email).first()
    if user:
        user_id = user.id
        user_validation_id = user.user_validation_id

        try:
            db_otp = db.query(OTP).filter(OTP.user_id == user_id).first()
            db_otp.otp = otp
            db_otp.otp_generated_datetime = otp_generated_datetime
            db_otp.otp_expiration_time = otp_expiration_time
            db.commit()
            db.refresh(db_otp)

            # Send email asynchronously
            await send_email(email, otp)

            data = {'user_validation_id': user_validation_id}
            return success_response(data)
        except Exception as e:
            db.rollback()
            print(f"Error updating OTP: {e}")
            return error_response(status_code=500, detail="Internal Server Error")
    else:
        data = {'user_validation_id': None }
        return success_response(data)
        
    
async def send_otp_email(email: str, db: Session):
    try:
        # Generate OTP
        otp = random.randint(1000, 9999)
        otp_generated_datetime = datetime.now()
        otp_expiration_time = otp_generated_datetime + timedelta(minutes=2)

        # Update OTP in the database
        user = db.query(User).filter(User.email == email).first()
        if user:
            user_id = user.id

            db_otp = db.query(OTP).filter(OTP.user_id == user_id).first()
            db_otp.otp = otp
            db_otp.otp_generated_datetime = otp_generated_datetime
            db_otp.otp_expiration_time = otp_expiration_time
            db.commit()
            db.refresh(db_otp)

            # Send email asynchronously
            msg = EmailMessage()
            msg['Subject'] = f'{otp} is your verification code'
            msg['From'] = email_address
            msg['To'] = email
            msg.set_content("Testing")

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(email_address, email_password)
                smtp.send_message(msg)

            data = {'user_validation_id': user.user_validation_id}
            return success_response(data)
        else:
            return error_response(status_code=404, detail="User not found")
    except Exception as e:
        print(f"Error sending OTP email: {e}")
        return error_response(status_code=500, detail="Internal Server Error")


def validate_email_format(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    return re.fullmatch(regex, email)

def generate_user_info(email):
    user_validation_id = secrets.token_hex(32)
    access_token = secrets.token_urlsafe(64)
    return user_validation_id, access_token

def add_user_to_db(db, email, user_validation_id):
    db_email = User(email=email, user_validation_id=user_validation_id)
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    return db_email


async def create_user_with_email_validation(email, db):
    user_email_in_db = db.query(User).filter(User.email == email).first()
    if user_email_in_db is None:
        user_validation_id, access_token = generate_user_info(email)
        db_email = add_user_to_db(db, email, user_validation_id)

        otp = random.randint(1000, 9999)
        otp_generated_datetime = datetime.now()
        otp_expiration_time = otp_generated_datetime + timedelta(minutes=2)
        user_id = db_email.id

        db_otp = OTP(otp=otp , otp_generated_datetime=otp_generated_datetime , otp_expiration_time=otp_expiration_time , user_id=user_id)
        db.add(db_otp)
        db.commit()
        db.refresh(db_otp)

        if await send_otp_email(email, otp):
            data = {'user_validation_id' : user_validation_id}
            return success_response(data)
        else:
            return error_response(status_code=500, detail="Error sending OTP email")
    else:
        return error_response(status_code=400 , detail='User already exists')
    








@router.post('/create-user') 
async def create_user(mail: Email, db: Session = Depends(get_db)): 
    email = mail.email
    
    if validate_email_format(email):
        return await create_user_with_email_validation(email, db)
    else:
        return error_response(status_code=400 , detail='Invalid Email')


        

@router.post('/validate_otp')
async def validate_otp( vo : ValidateOtp , db: Session = Depends(get_db)) : 
    otp = vo.otp
    user_validation_id = vo.user_validation_id
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
                return error_response(status_code=400 , detail='Your OTP has expired.')
            else:
                return error_response(status_code=400 , detail='Invalid OTP')
 



@router.post('/resend_otp')
async def resend_otp(us: Us, db: Session = Depends(get_db)) : 
    user_validation_id = us.user_validation_id
    user = db.query(User).filter(User.user_validation_id == user_validation_id).first()
    
    if user:
        try:
            # Send OTP email
            response = await send_otp_email(user.email, db)
            return response
        except Exception as e:
            print(f"Error resending OTP: {e}")
            return error_response(status_code=500, detail="Internal Server Error")
    else:
        return error_response(status_code=400 , detail='Invalid email')

 



class UserNotFoundOrAlreadyRegisteredError(Exception):
    def __init__(self, detail):
        self.detail = detail
        
@router.post('/register')
async def register(user_info: User_info, access_token: str = Header(None), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.access_token == access_token).first()
    print(f"User: {user}")
    if user:
        print(f"user.email: {user.email}")
        print(f"user_info.email: {user_info.email}")
        print(f"user.is_registered: {user.is_registered}")
    if user and user.email == user_info.email and user.is_registered == False:
        print(user_info.email)
        # if len(user_info.profile_photo.encode('utf-8')) <= 2 * 1024 * 1024:
        user.first_name = user_info.first_name
        user.last_name = user_info.last_name
        user.profile_photo = user_info.profile_photo
        user.country_code = user_info.country_code
        user.phone_no = user_info.phone_no
        user.access_token = secrets.token_urlsafe(64)
        user.is_registered = True
        db.commit()
        data = {'access_token': user.access_token}
        return success_response(data)
    else:
        error_response(status_code=400 , detail="User not found or already registered")

    
    
@router.post("/login")
async def login(mail: Email, db: Session = Depends(get_db)):
    email = mail.email
    print("Valid Email")
    try:
        return await handle_login(email, db)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Unhandled error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    
