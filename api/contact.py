"""
Embodied Awareness — /api/contact
Handles contact form submissions and sends email via Gmail SMTP.
Environment variables required in Vercel:
  GMAIL_APP_PASSWORD  — Google App Password for embodied.awareness.no@gmail.com
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = "embodied.awareness.no@gmail.com"
GMAIL_TO   = "embodied.awareness.no@gmail.com"


def send_email(name: str, email: str, topic: str, message: str) -> None:
    password = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not password:
        raise RuntimeError("GMAIL_APP_PASSWORD not set")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[Embodied Awareness] {topic} – {name}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = GMAIL_TO
    msg["Reply-To"] = email

    body = f"""\
Ny henvendelse fra embodiedawareness.no

Navn:    {name}
E-post:  {email}
Gjelder: {topic}

{message}
"""
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, password)
        server.sendmail(GMAIL_USER, GMAIL_TO, msg.as_string())


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)
            data = json.loads(raw)

            name    = data.get("name", "").strip()
            email   = data.get("email", "").strip()
            topic   = data.get("topic", "Generell henvendelse").strip()
            message = data.get("message", "").strip()

            if not name or not email:
                self._respond(400, {"ok": False, "error": "Name and email required"})
                return

            send_email(name, email, topic, message)
            self._respond(200, {"ok": True})

        except Exception as e:
            self._respond(500, {"ok": False, "error": str(e)})

    def _respond(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "https://embodiedawareness.no")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, *args):
        pass
