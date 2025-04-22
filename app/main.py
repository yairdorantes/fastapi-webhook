from fastapi import FastAPI, Request, Depends
import subprocess
from models import Script
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from pydantic import BaseModel
import imaplib
import email
from email.header import decode_header
import requests
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from loguru import logger
from apscheduler.schedulers.background import (
    BackgroundScheduler,
)

from apscheduler.triggers.cron import (
    CronTrigger,
)

from email.utils import parseaddr

from apscheduler.triggers.interval import IntervalTrigger

app = FastAPI()


load_dotenv()

email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_PASS")
webhook_url = os.getenv("WEBHOOK_URL")
imap_server = os.getenv("IMAP_SERVER")

logger.info(
    f"Initializing values... {email_user} | {email_pass} | {webhook_url} | {imap_server}"
)

email_blacklist = ("Trello", "notifications@openproject.com", "Microsoft")


def send_whatsapp_message(email_text: str):
    data = {"new_email": email_text}
    requests.post(webhook_url, json=data)


def check_unread_emails(username: str, password: str, imap_server=imap_server):
    print("Checking for new emails...")
    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(username, password)
        mail.select("inbox", readonly=True)
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK":
            print("Error buscando correos no leídos.")
            return
        for num in messages[0].split():
            status, data = mail.fetch(num, "(BODY[HEADER.FIELDS (FROM SUBJECT DATE)])")
            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")
                    name, _ = parseaddr(msg["From"])
                    print(f"You got a new emal from: {name}, Subject: {subject}")
                    email_text = (
                        f"You got a new email from: *{name}*, Subject: *{subject}*"
                    )
                    if name not in email_blacklist:
                        print(f"Sending message to WhatsApp: {email_text}")
                        send_whatsapp_message(email_text)
        mail.logout()
    except Exception as e:
        print(f"Error al revisar correos: {e}")


scheduler = BackgroundScheduler()
trigger = CronTrigger(day_of_week="mon-fri", hour="5-23", minute=0)
# trigger = IntervalTrigger(seconds=5)
scheduler.add_job(lambda: check_unread_emails(email_user, email_pass), trigger)
scheduler.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    scheduler.shutdown()


Base.metadata.create_all(bind=engine)


class ScriptData(BaseModel):
    name: str
    description: str | None = None  # optional field


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/webhook/{script_id}")
async def webhook(request: Request, script_id: int, db: Session = Depends(get_db)):
    result = db.query(Script).filter(Script.id == script_id).first()
    if result:
        print(f"Script found: {result.name}")
        run_script = subprocess.run(
            ["bash", f"../scripts/{result.name}.sh"],
        )
    else:
        print(f"Script with ID {script_id} not found")

    return {"message": "Webhook received successfully"}


@app.post("/scripts")
async def create_script(data: ScriptData, db: Session = Depends(get_db)):
    new_script = Script(name=data.name)
    db.add(new_script)
    db.commit()
    db.refresh(new_script)
    return {"message": "Script created successfully", "id": new_script.id}


@app.get("/health")
async def health_check():
    subprocess.run(
        ["bash", f"/app/scripts/ws.sh"],
    )

    return {"status": "healthy"}
