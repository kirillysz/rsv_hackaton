import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

from app.utils.yougile.executor import YouGileExecutor
from app.utils.yougile.service import YougileClient
from app.llm.service import LLMService

from app.bot.evening_sync import router

from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = AiohttpSession(proxy="socks5://127.0.0.1:10808")
bot = Bot(token=settings.BOT_TOKEN, session=session)
dp = Dispatcher()
ollama = LLMService(model="qwen2.5:3b")

yc = YougileClient(token=settings.YOUGILE_TOKEN)
executor = YouGileExecutor(client=yc)

SUMMARY_PROMPT = """\
Ты — ассистент-аналитик рабочего чата.
Напиши саммари переписки: о чём говорили, какие задачи упомянуты, 
кто за что отвечает, какие дедлайны названы.
Отвечай на русском, кратко и по делу.
"""

message_buffer: list[str] = []


@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def collect(message: types.Message):
    if not message.text:
        return
    
    name = message.from_user.full_name if message.from_user else "unknown"
    date = message.date.strftime("%Y-%m-%d %H:%M:%S")
    message_buffer.append(f"[{date}] {name}: {message.text}")


@dp.message(Command("summary"))
async def cmd_summary(message: types.Message):
    if not message_buffer:
        await message.reply("Пока нет сообщений для саммари.")
        return

    await message.reply("Генерирую саммари...")
    chat_text = "\n".join(message_buffer[-200:])

    from ollama import AsyncClient

    raw_ollama = AsyncClient()
    summary_response = await raw_ollama.chat(
        model="qwen2.5:3b",
        messages=[
            {"role": "system", "content": SUMMARY_PROMPT},
            {"role": "user", "content": f"Переписка:\n\n{chat_text}"},
        ],
    )
    summary_text = summary_response.message.content
    await message.reply(summary_text)

    result = await ollama.chat(
        messages=[{"role": "user", "content": summary_text}]
    )

    if result["error"]:
        logger.error("LLM error: %s", result["error"])
        return

    parsed = result["parsed"]
    print(parsed)

    exec_result = await executor.execute(parsed)
    logger.info("Executor result: %s", exec_result)

    created = [r for r in exec_result if r.get("ok")]
    if created:
        await message.reply(f"✅ Создано задач в YouGile: {len(created)}")

    message_buffer.clear()

async def main():
    me = await bot.get_me()
    logger.info("Bot identity: @%s (id=%s)", me.username, me.id)
    
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())