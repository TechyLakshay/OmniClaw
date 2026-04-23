from bot.notifier import send_high_priority_notification


def send_telegram_message(text: str) -> str:
    return send_high_priority_notification("", "", text)
