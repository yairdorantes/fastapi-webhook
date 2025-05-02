from fastapi import FastAPI, Request, Depends
import subprocess
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
import json
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import Project

app = FastAPI()


load_dotenv()

email_user = os.getenv("EMAIL_USER")
email_pass = os.getenv("EMAIL_PASS")
webhook_url = os.getenv("WEBHOOK_URL")
imap_server = os.getenv("IMAP_SERVER")

Base.metadata.create_all(bind=engine)

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


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    return {"status": "healthy"}


@app.post("/deploy/")
async def deploy_CICD(project_id: int, db: Session = Depends(get_db)):
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            result = subprocess.run(
                ["bash", project.path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            return {"status": "healthy", "output": result.stdout.strip()}
        else:
            return {"status": "Error", "message": "project not found"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "output": e.stderr.strip()}
