"""
Embodied Awareness — /api/contact
Sends contact form submissions via Resend API.
Environment variable required in Vercel:
  RESEND_API_KEY  — API key from resend.com
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

RESEND_API = "https://api.resend.com/emails"
TO_EMAIL   = "embodied.awareness.no@gmail.com"
FROM_EMAIL = "onboarding@resend.dev"


def send_email(name: str, email: str, topic: str, message: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        raise RuntimeError("RESEND_API_KEY not set")

    payload = json.dumps({
        "from":     FROM_EMAIL,
        "to":       [TO_EMAIL],
        "reply_to": email,
        "subject":  f"[Embodied Awareness] {topic} – {name}",
        "text":     f"Navn: {name}\nE-post: {email}\nGjelder: {topic}\n\n{message}"
    }).encode()

    req = urllib.request.Request(
        RESEND_API,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        if resp.status not in (200, 201):
            raise RuntimeError(f"Resend error {resp.status}")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length  = int(self.headers.get("Content-Length", 0))
            data    = json.loads(self.rfile.read(length))
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
        self.send_header("Content-Type",   "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin",  "https://embodiedawareness.no")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, *args):
        pass
