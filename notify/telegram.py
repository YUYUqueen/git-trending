from __future__ import annotations
import logging
from telegram import Bot
import config
from analyzer.reporter import format_daily_telegram

logger = logging.getLogger(__name__)


async def send_report(report: str):
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    chat_id = config.TELEGRAM_CHAT_ID
    messages = format_daily_telegram(report)
    for msg in messages:
        await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML", disable_web_page_preview=True)
    logger.info("Sent %d message(s) to Telegram", len(messages))


async def send_alert(text: str):
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    await bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text=f"\u26a0\ufe0f <b>Alert</b>\n\n{text}",
        parse_mode="HTML",
    )
