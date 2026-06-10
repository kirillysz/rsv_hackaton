import asyncio
import html
import logging
import re
import uuid
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.evening_sync import router, setup_scheduler
from app.llm.service import LLMService
from app.utils.yougile.executor import YouGileExecutor
from app.utils.yougile.service import YougileClient

from telemost_run import run_tm
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

session = AiohttpSession(proxy="socks5://127.0.0.1:10808")

bot = Bot(
    token=settings.BOT_TOKEN,
    session=session
)

dp = Dispatcher()

ollama = LLMService(model="qwen2.5:3b")

yc = YougileClient(
    token=settings.YOUGILE_TOKEN
)

executor = YouGileExecutor(client=yc)
user_states = {}

SUMMARY_PROMPT = """
Ты — ассистент-аналитик рабочего чата.

Напиши саммари переписки:
- о чем говорили
- какие задачи появились
- кто ответственный
- какие дедлайны названы

Отвечай кратко и по делу.
"""

message_buffer: list[str] = []

pending_tasks: dict[str, dict] = {}



@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def collect(message: types.Message):
    if not message.text:
        return

    name = (
        message.from_user.full_name
        if message.from_user
        else "unknown"
    )

    dt = message.date.strftime("%Y-%m-%d %H:%M:%S")

    message_buffer.append(
        f"[{dt}] {name}: {message.text}"
    )



def format_deadline(deadline_value):
    if not deadline_value:
        return "Не указан"

    try:
        if isinstance(deadline_value, dict):
            deadline_value = deadline_value.get("deadline")

        return datetime.fromtimestamp(
            deadline_value / 1000
        ).strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(deadline_value)


def build_preview_text(parsed: dict) -> str:
    actions = parsed.get("actions", [])

    text = "📋 <b>Задачи из встречи</b>\n\n"

    if not actions:
        text += "Задачи не найдены."
        return text

    task_num = 1
    for action in actions:
        action_type = action.get("type")

        if action_type == "create_task":
            title = html.escape(action.get("title", "Без названия"))
            deadline = format_deadline(action.get("deadline"))
            assigned = action.get("assigned", [])
            assigned_text = ", ".join(assigned) if assigned else "Не назначен"
            description = html.escape(action.get("description", ""))

            text += (
                f"<b>{task_num}. {title}</b>\n"
                f"👤 Ответственный: {assigned_text}\n"
                f"📅 Дедлайн: {deadline}\n"
            )

            if description:
                text += f"📝 {description}\n"

            text += "\n"
            task_num += 1

        elif action_type == "set_task_complete":
            task_id = html.escape(action.get("task_id", ""))
            text += f"✅ <i>Отметить задачу выполненной: <code>{task_id}</code></i>\n\n"

    return text

async def notify_admin(
    approval_id: str,
    parsed: dict
):
    builder = InlineKeyboardBuilder()

    builder.button(
        text="✅ Подтвердить",
        callback_data=f"confirm:{approval_id}"
    )

    builder.button(
        text="❌ Отклонить",
        callback_data=f"reject:{approval_id}"
    )

    builder.adjust(2)

    await bot.send_message(
        chat_id=settings.ADMIN_ID,
        text=build_preview_text(parsed),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@dp.message(Command("summary"))
async def cmd_summary(message: types.Message):

    if not message_buffer:
        await message.reply(
            "Пока нет сообщений для саммари."
        )
        return

    await message.reply(
        "Генерирую саммари..."
    )

    chat_text = "\n".join(
        message_buffer[-200:]
    )

    from ollama import AsyncClient

    raw_ollama = AsyncClient()

    summary_response = await raw_ollama.chat(
        model="qwen2.5:3b",
        messages=[
            {
                "role": "system",
                "content": SUMMARY_PROMPT
            },
            {
                "role": "user",
                "content": (
                    f"Переписка:\n\n{chat_text}"
                )
            }
        ]
    )

    summary_text = (
        summary_response.message.content
    )

    await message.reply(summary_text)

    result = await ollama.chat(
        messages=[
            {
                "role": "user",
                "content": summary_text
            }
        ]
    )

    if result["error"]:
        logger.error(
            "LLM error: %s",
            result["error"]
        )

        await message.reply(
            "Ошибка обработки задач."
        )

        return

    parsed = result["parsed"]

    logger.info(
        "Parsed result: %s",
        parsed
    )

    approval_id = str(uuid.uuid4())

    pending_tasks[approval_id] = parsed

    await notify_admin(
        approval_id=approval_id,
        parsed=parsed
    )


    message_buffer.clear()

@dp.message(Command("telemost"))
async def telemost_start(message: types.Message):
    user_states[message.from_user.id] = "waiting_url"
    await message.answer("Пришли URL для обработки 🎥")

@dp.message(lambda m: m.from_user and user_states.get(m.from_user.id) == "waiting_url")
async def handle_telemost_url(message: types.Message):
    user_id = message.from_user.id
    url = message.text.strip()
    user_states[user_id] = None

    await message.answer("Принял URL, начинаю обработку... ⏳")

    try:
        await message.answer("📡 Запускаю запись и анализ...")

        result = await run_tm(url)

        task_id = result[0].get("id") if isinstance(result, list) else result.get("id")
        task = await yc.get_task(task_id=task_id) 

        title       = task.get("title", "Без названия")
        deadline    = format_deadline(task.get("deadline"))
        assigned    = task.get("assigned", [])
        assigned_text = ", ".join(assigned) if assigned else "Не назначен"
        label       = task.get("idTaskProject") or task.get("idTaskCommon", "")

        await message.answer(
            f"Готово ✅\n\n"
            f"<b>{label}: {html.escape(title)}</b>\n"
            f"👤 Ответственный: {html.escape(assigned_text)}\n"
            f"📅 Дедлайн: {deadline}",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.exception(e)
        await message.answer(f"Ошибка ❌: {e}")

@dp.callback_query(
    F.data.startswith("confirm:")
)
async def confirm_task(
    callback: types.CallbackQuery
):

    approval_id = callback.data.split(
        ":",
        1
    )[1]

    parsed = pending_tasks.get(
        approval_id
    )

    if not parsed:
        await callback.answer(
            "Уже обработано."
        )
        return

    try:

        exec_result = await executor.execute(
            parsed
        )

        logger.info(
            "Created tasks: %s",
            exec_result
        )

        pending_tasks.pop(
            approval_id,
            None
        )

        await callback.message.edit_text(
            callback.message.text
            + "\n\n✅ <b>Подтверждено и создано в YouGile</b>",
            parse_mode="HTML"
        )

        await callback.answer(
            "Задачи созданы."
        )

    except Exception as e:

        logger.exception(e)

        await callback.answer(
            "Ошибка создания задач.",
            show_alert=True
        )

@dp.callback_query(
    F.data.startswith("reject:")
)
async def reject_task(
    callback: types.CallbackQuery
):

    approval_id = callback.data.split(
        ":",
        1
    )[1]

    pending_tasks.pop(
        approval_id,
        None
    )

    await callback.message.edit_text(
        callback.message.text
        + "\n\n❌ <b>Отклонено</b>",
        parse_mode="HTML"
    )

    await callback.answer(
        "Отклонено."
    )


async def main():

    me = await bot.get_me()

    logger.info(
        "Bot identity: @%s (id=%s)",
        me.username,
        me.id
    )

    await bot.set_my_commands([
        types.BotCommand(
            command="summary",
            description="Саммари встречи"
        ),
        types.BotCommand(
            command="sync_now",
            description="Вечерний синхрон"
        ),
        types.BotCommand(
            command="telemost",
            description="Запись созвона в Телемост"
        )
    ])

    dp.include_router(router)
    scheduler = setup_scheduler(bot)
    scheduler.start()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())