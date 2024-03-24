from fastapi import APIRouter , Depends , Header
from models import User 
from sqlalchemy.orm import Session
import secrets
import smtplib
from database import get_db

from email.message import EmailMessage


router = APIRouter(
    prefix='/account'
)




@router.get('/get_user')
async def get_user(access_token: str = Header(None) ,  db: Session = Depends(get_db)) : 
    user = db.query(User).filter(User.access_token == access_token).first()
    
    return {
        'first_name' : user.first_name , 
        'last_name' : user.last_name , 
        'profile_photo' : user.profile_photo ,
        'country_code' : user.country_code , 
        'phone_no' : user.phone_no   , 
        'email' : user.email
    }

