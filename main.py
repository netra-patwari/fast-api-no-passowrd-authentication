from uvicorn import run
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from email.message import EmailMessage
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware


from routes.authentication import router as auth_router
from routes.account import router as account_router 
load_dotenv()


app = FastAPI()







app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)








app.include_router(auth_router)
app.include_router(account_router)

email_address = os.getenv('EMAIL_ADD')
email_password = os.getenv('EMAIL_PASS') 

msg = EmailMessage()



@app.get('/')
async def root():
    return { 'working' : 'Hell Yes!!' }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": {}, "meta": {"status": exc.status_code, "message": exc.detail}},
    )









