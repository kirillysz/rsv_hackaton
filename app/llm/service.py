import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from ollama import AsyncClient
from app.llm.prompt import PROMPT


class LLMService:
    def __init__(
        self,
        model: str = "qwen2.5:3b",
        timezone: str = "Europe/Warsaw",
    ):
        self.client = AsyncClient()
        self.model = model
        self.prompt = PROMPT
        self.tz = ZoneInfo(timezone)

        # Словарь для русских месяцев (родительный падеж)
        self.months_rus = {
            'января': 1, 'февраля': 2, 'марта': 3, 'апреля': 4,
            'мая': 5, 'июня': 6, 'июля': 7, 'августа': 8,
            'сентября': 9, 'октября': 10, 'ноября': 11, 'декабря': 12
        }

    def _parse_json(self, text: str) -> dict:
        """Извлекает JSON из ответа модели, даже если он обёрнут в лишний текст."""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1:
                raise ValueError("No JSON found in output")
            return json.loads(text[start:end + 1])

    def _normalize_deadline(self, dl):
        """
        Единый стандарт дедлайна:
        - всегда возвращаем int (миллисекунды) или None
        - из строк (если вдруг пришли) пытаемся достать число
        """
        if dl is None:
            return None
        if isinstance(dl, (int, float)):
            dl = int(dl)
            # если вдруг секунды – переводим в мс
            if dl < 10**12:
                dl *= 1000
            return dl
        if isinstance(dl, str):
            dl = dl.strip()
            if dl.isdigit():
                return self._normalize_deadline(int(dl))
        return None

    def _replace_dot_date(self, match: re.Match) -> str:
        day, month, year_str = match.group(1), match.group(2), match.group(3)
        year = int(year_str)
        if year < 100:
            year += 2000

        dt = datetime(year, int(month), int(day), tzinfo=self.tz)
        ts_ms = int(dt.timestamp() * 1000)
        return f"{match.group(0)} (UNIX {ts_ms} мс)"

    def _replace_rus_date(self, match: re.Match) -> str:

        day = int(match.group(1))
        month_name = match.group(2)
        month = self.months_rus[month_name]
        year_str = match.group(3)

        if year_str:
            year = int(year_str)
        else:
            year = datetime.now(self.tz).year

        dt = datetime(year, month, day, tzinfo=self.tz)
        ts_ms = int(dt.timestamp() * 1000)
        return f"{match.group(0)} (UNIX {ts_ms} мс)"

    def _preprocess_user_message(self, text: str) -> str:
        date_pattern_dots = r'\b(\d{2})\.(\d{2})\.(\d{2,4})\b'
        text = re.sub(date_pattern_dots, self._replace_dot_date, text)

        month_names = '|'.join(self.months_rus.keys())
        rus_pattern = rf'(\d{{1,2}})\s+({month_names})\s*(?:\(?\s*(\d{{4}})\s*(?:года)?\s*\)?)?'
        text = re.sub(rus_pattern, self._replace_rus_date, text)

        return text

    async def chat(self, messages: list[dict], context: dict | None = None) -> dict:
        for msg in messages:
            if msg.get("role") == "user":
                msg["content"] = self._preprocess_user_message(msg["content"])

        now = datetime.now(self.tz)

        system_time = {
            "role": "system",
            "content": (
                "ТЕКУЩЕЕ ВРЕМЯ:\n"
                f"- UNIX ms: {int(now.timestamp() * 1000)}\n\n"
                "ВСЕ дедлайны должны быть только UNIX timestamp в миллисекундах.\n"
                "Никаких строк, только число или null.\n"
                "Если в сообщении пользователя дата уже снабжена числом в скобках "
                "(например, '09 июня (2026 года) (UNIX 1781042400000 мс)'), "
                "то бери это число как есть, без пересчёта."
            ),
        }

        full_messages = [
            system_time,
            self.prompt,
            *messages,
        ]

        response = await self.client.chat(
            model=self.model,
            messages=full_messages,
            format="json",
        )

        content = response["message"]["content"]
        parsed = self._parse_json(content)

        if "actions" not in parsed:
            return {
                "raw": content,
                "parsed": parsed,
                "error": "Missing actions",
            }

        for action in parsed.get("actions", []):
            if action.get("type") == "create_task":
                action["deadline"] = self._normalize_deadline(
                    action.get("deadline")
                )

        return {
            "raw": content,
            "parsed": parsed,
            "error": None,
        }