import json
import time
import anthropic
from llm.base import LLMClient
from config.settings import settings

MODEL = "claude-sonnet-4-20250514"
MAX_RETRIES = 3


class AnthropicClient(LLMClient):
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(self, prompt: str, system: str = None) -> str:
        kwargs = {
            "model": MODEL,
            "max_tokens": 2048,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        for attempt in range(MAX_RETRIES):
            try:
                response = self._client.messages.create(**kwargs)
                return response.content[0].text
            except anthropic.RateLimitError:
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2 ** attempt)

    def generate_json(self, prompt: str, system: str = None, schema: dict = None) -> dict:
        system_parts = [system] if system else []
        system_parts.append("Respond with valid JSON only. Do not include markdown formatting or code fences.")
        if schema:
            system_parts.append(f"The response must conform to this schema: {json.dumps(schema)}")
        full_system = "\n".join(system_parts)

        raw = self.generate(prompt, system=full_system)
        raw = raw.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            lines = raw.split("\n")
            # Remove opening fence line and closing fence
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            raw = "\n".join(inner).strip()

        return json.loads(raw)
