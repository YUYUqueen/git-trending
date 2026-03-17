from __future__ import annotations
import logging
from telegram import Bot
import config

logger = logging.getLogger(__name__)

TELEGRAM_MAX_LENGTH = 4096


def _split_message(text: str) -> list[str]:
    """Split long messages at newline boundaries to fit Telegram's 4096 char limit."""
    if len(text) <= TELEGRAM_MAX_LENGTH:
        return [text]
    messages = []
    while text:
        if len(text) <= TELEGRAM_MAX_LENGTH:
            messages.append(text)
            break
        split_at = text.rfind("\n", 0, TELEGRAM_MAX_LENGTH)
        if split_at == -1:
            split_at = TELEGRAM_MAX_LENGTH
        messages.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return messages


async def send_report(report: str):
    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
    chat_id = config.TELEGRAM_CHAT_ID
    messages = _split_message(report)
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
