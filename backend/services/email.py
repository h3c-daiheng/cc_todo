import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from cryptography.fernet import Fernet
import base64
from config import SECRET_KEY

logger = logging.getLogger(__name__)

def _get_fernet() -> Fernet:
    # 用 SECRET_KEY 派生 32 字节 base64 key
    key = base64.urlsafe_b64encode(SECRET_KEY.encode()[:32].ljust(32, b'0'))
    return Fernet(key)

def encrypt_password(plain: str) -> str:
    return _get_fernet().encrypt(plain.encode()).decode()

def decrypt_password(cipher: str) -> str:
    return _get_fernet().decrypt(cipher.encode()).decode()

def get_smtp_config(db) -> dict | None:
    from models import SystemSetting
    keys = ["smtp_host", "smtp_port", "smtp_username", "smtp_password", "smtp_from", "email_send_hour"]
    settings = {s.key: s.value for s in db.query(SystemSetting).filter(SystemSetting.key.in_(keys)).all()}
    if not settings.get("smtp_host"):
        return None
    if settings.get("smtp_password"):
        try:
            settings["smtp_password"] = decrypt_password(settings["smtp_password"])
        except Exception:
            pass
    return settings

def send_email(to: str, subject: str, body: str, config: dict):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config["smtp_from"]
    msg["To"] = to
    msg.attach(MIMEText(body, "html", "utf-8"))
    port = int(config.get("smtp_port", 25))
    with smtplib.SMTP(config["smtp_host"], port, timeout=10) as server:
        if config.get("smtp_username") and config.get("smtp_password"):
            server.login(config["smtp_username"], config["smtp_password"])
        server.send_message(msg)
    logger.info(f"邮件已发送至 {to}")
