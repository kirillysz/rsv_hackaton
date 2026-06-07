import json

from ollama import AsyncClient
from datetime import datetime, timezone
from app.llm.prompt import PROMPT


class LLMService:
    def __init__(self, model: str = "llama3"):
        self.client = AsyncClient(  )
        self.model = model
        self.prompt = PROMPT

    async def chat(self, messages: list[dict], context: dict | None = None) -> dict:
        now = datetime.now(timezone.utc)

        now_iso = now.strftime("%Y-%m-%d %H:%M:%S UTC")
        now_ms = int(now.timestamp() * 1000)

        system_time = {
            "role": "system",
            "content": f"""
                ТЕКУЩЕЕ ВРЕМЯ (ОБЯЗАТЕЛЬНО):

                - Сейчас (ISO): {now_iso}
                - Сейчас (UNIX ms): {now_ms}

                ВСЕ ОТНОСИТЕЛЬНЫЕ ДАТЫ СЧИТАЙ ОТ ЭТОГО МОМЕНТА.
                """
        }

        full_messages = [
            system_time,
            self.prompt,
            *messages
        ]

        response = await self.client.chat(
            model=self.model,
            messages=full_messages
        )

        content = response["message"]["content"]

        try:
            parsed = json.loads(content)
        except Exception:
            return {
                "raw": content,
                "parsed": None,
                "error": "Invalid JSON from model"
            }

        if "actions" not in parsed:
            return {
                "raw": content,
                "parsed": parsed,
                "error": "No actions field"
            }

        return {
            "raw": content,
            "parsed": parsed,
            "error": None
        }