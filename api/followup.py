"""
ClearDoc — /api/followup
Handles follow-up questions about a previously submitted document.
Deployed as a Vercel Python Serverless Function.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import anthropic

SYSTEM_PROMPT = """You are ClearDoc, a helpful document analysis assistant. The user has already had their
document analyzed and is now asking follow-up questions about it.

Answer questions clearly and directly in plain language. Be specific to the document they shared.
Keep answers concise — 2-5 sentences is usually enough.

Important:
- Always refer back to the specific document content in your answers.
- If you can't answer from the document, say so honestly.
- Never give legal advice that requires professional judgment — but do explain what the document says clearly.
- Do NOT be overly cautious or hedge every sentence. People need real, useful answers."""


class handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            document_text = data.get("document_text", "").strip()
            document_type = data.get("document_type", "document").strip()
            history = data.get("conversation_history", [])

            if not document_text or not history:
                self._respond(400, {"error": "document_text and conversation_history are required"})
                return

            # Cap document length
            if len(document_text) > 12000:
                document_text = document_text[:12000] + "\n\n[Document truncated]"

            # Build message history with document as context in first user message
            messages = []
            for i, turn in enumerate(history):
                role = turn.get("role", "user")
                content = turn.get("content", "")
                if i == 0 and role == "user":
                    # Prepend document context to first message
                    content = (
                        f"Here is the {document_type} I want to ask about:\n\n"
                        f"{document_text}\n\n"
                        f"My question: {content}"
                    )
                messages.append({"role": role, "content": content})

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                self._respond(500, {"error": "API key not configured"})
                return

            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model="claude-haiku-4-5-20251001",  # Faster + cheaper for quick Q&A
                max_tokens=512,
                system=SYSTEM_PROMPT,
                messages=messages
            )

            answer = message.content[0].text.strip()
            self._respond(200, {"answer": answer})

        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)
