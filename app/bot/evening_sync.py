import logging

from aiogram import Bot, Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.utils.yougile.service import YougileClient
from config import settings

logger = logging.getLogger(__name__)
router = Router()

SYNC_HOUR = 18
SYNC_MINUTE = 0


def build_task_keyboard(task_id: str) -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Готово",    callback_data=f"done:{task_id}")
    builder.button(text="⏳ В работе", callback_data=f"wip:{task_id}")
    builder.adjust(2)
    return builder.as_markup()


async def send_evening_sync(bot: Bot) -> None:
    yc = YougileClient(token=settings.YOUGILE_TOKEN)
    tasks = await yc.get_tasks(column_id=settings.COLUMN_ID)

    active = [t for t in tasks if not t.get("completed") and not t.get("deleted")]

    if not active:
        await bot.send_message(
            chat_id=settings.FORUM_SYNC_ID,
            message_thread_id=settings.FORUM_SYNC_THREAD_ID,
            text="🌆 *Вечерний синхрон*\n\nАктивных задач нет — отдыхаем! 🎉",
            parse_mode="Markdown",
        )
        return

    await bot.send_message(
        chat_id=settings.FORUM_SYNC_ID,
        message_thread_id=settings.FORUM_SYNC_THREAD_ID,
        text="🌆 *Вечерний синхрон!*\nОтметьте статус своих задач:",
        parse_mode="Markdown",
    )

    for task in active:
        task_id    = task["id"]
        title      = task.get("title", "Без названия")
        project_id = task.get("idTaskProject", "")

        deadline_line = ""
        if dl := task.get("deadline", {}).get("deadline"):
            from datetime import datetime, timezone
            dt = datetime.fromtimestamp(dl / 1000, tz=timezone.utc)
            deadline_line = f"\n📅 до {dt.strftime('%d.%m')}"

        text = f"📌 *{title}*\n🔖 {project_id}{deadline_line}"

        await bot.send_message(
            chat_id=settings.FORUM_SYNC_ID,
            message_thread_id=settings.FORUM_SYNC_THREAD_ID,
            text=text,
            parse_mode="Markdown",
            reply_markup=build_task_keyboard(task_id),
        )


@router.callback_query(F.data.startswith("done:"))
async def on_task_done(callback: types.CallbackQuery) -> None:
    task_id = callback.data.split(":", 1)[1]
    yc = YougileClient(token=settings.YOUGILE_TOKEN)

    try:
        await yc.set_task_complete(task_id=task_id)
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ *Выполнено!*",
            parse_mode="Markdown",
            reply_markup=None,
        )
        await callback.answer("Закрыто в YouGile!")
    except Exception as e:
        logger.error(f"Ошибка при закрытии {task_id}: {e}")
        await callback.answer("Ошибка при обновлении", show_alert=True)


@router.callback_query(F.data.startswith("wip:"))
async def on_task_wip(callback: types.CallbackQuery) -> None:
    await callback.answer("Окей, остаётся в работе.")


@router.message(Command("sync_now"))
async def cmd_sync_now(message: types.Message, bot: Bot) -> None:
    await message.reply("🔄 Запускаю вечерний синхрон...")
    await send_evening_sync(bot)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        send_evening_sync,
        trigger="cron",
        hour=SYNC_HOUR,
        minute=SYNC_MINUTE,
        args=[bot],
        id="evening_sync",
        replace_existing=True,
    )
    return scheduler