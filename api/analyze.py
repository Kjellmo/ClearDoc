"""
ClearDoc — /api/analyze
Receives a document, calls Claude, returns a structured analysis.
Deployed as a Vercel Python Serverless Function.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import anthropic

SYSTEM_PROMPT = """You are ClearDoc, an expert document analyst. Your job is to help ordinary people
understand complex legal, financial, and formal documents — in plain, simple language.

When given a document, you will return a JSON object with EXACTLY this structure (no markdown, no code fences, raw JSON only):

{
  "summary": "A clear 2-3 paragraph summary of what this document says and what it means for the person reading it. Write as if explaining to a smart friend who is not a lawyer.",
  "key_terms": [
    {
      "term": "The legal or technical term as it appears in the document",
      "explanation": "A plain-language explanation of what this means in practice"
    }
  ],
  "red_flags": [
    {
      "clause": "The exact problematic phrase or clause from the document (keep it short)",
      "explanation": "Why this matters and what risk or issue it creates for the reader",
      "severity": "high | medium | low"
    }
  ],
  "questions": [
    "A specific question the reader should ask before signing or accepting this document"
  ]
}

Rules:
- key_terms: include 3-7 of the most important or confusing terms. Skip if none.
- red_flags: only include genuine concerns. Use 'high' for things that could cause real harm, 'medium' for things worth clarifying, 'low' for minor oddities. Skip if there are truly no concerns.
- questions: include 3-6 specific, practical questions. These should be questions the reader can actually ask the other party.
- Always write from the perspective of protecting the person who is reading and signing the document.
- Be honest — if something is genuinely problematic, say so clearly.
- Do NOT include legal disclaimers or hedge everything. People need clear answers.
- Return ONLY valid JSON. No explanation outside the JSON."""


class handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Suppress default logging

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
            # Parse request
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)

            document_text = data.get("document_text", "").strip()
            document_type = data.get("document_type", "document").strip()

            if not document_text:
                self._respond(400, {"error": "document_text is required"})
                return

            # Cap at ~12,000 chars to keep costs low (~3,000 tokens)
            if len(document_text) > 12000:
                document_text = document_text[:12000] + "\n\n[Document truncated for analysis]"

            # Call Claude
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                self._respond(500, {"error": "API key not configured"})
                return

            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"Please analyze this {document_type}:\n\n{document_text}"
                    }
                ]
            )

            raw = message.content[0].text.strip()

            # Strip code fences if Claude added them
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            result = json.loads(raw)
            self._respond(200, result)

        except json.JSONDecodeError as e:
            self._respond(500, {"error": f"Failed to parse AI response: {str(e)}", "raw": raw if 'raw' in dir() else ""})
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
