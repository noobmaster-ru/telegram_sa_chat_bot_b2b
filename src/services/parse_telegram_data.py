import json
from pathlib import Path

def parse_telegram_export(json_path: str, output_path: str = None) -> None:
    """Парсит Telegram export .json и сохраняет данные по каждому собеседнику в parsed_data.json."""
    if output_path is None:
        output_path = Path(json_path).with_name("parsed_data.json")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    chats = data.get("chats", {}).get("list", [])
    results = {}
    skip_telegram_id = [777000,547299317,694144143]
    for chat in chats:
        name = chat.get("name") or chat.get("title") or "Unknown"
        telegram_id = chat.get("id") 
        type = chat.get("type")
        if (not telegram_id in skip_telegram_id) and type == "personal_chat":
            messages = chat.get("messages", [])
            dialog = []

            for msg in messages:
                if msg.get("type") != "message":
                    continue

                sender = msg.get("from", "")
                text = msg.get("text", "")
                date = msg.get("date")

                # Telegram иногда хранит text как список (текст + эмодзи/ссылки)
                if isinstance(text, list):
                    text = "".join(
                        [t if isinstance(t, str) else t.get("text", "") for t in text]
                    )

                # Приводим метку отправителя к понятному виду
                sender_label = "me" if sender == "Ты" else sender

                dialog.append({
                    "from": sender_label,
                    "text": text,
                    "date": date
                })

            # Сортируем диалог по дате (на всякий случай)
            # dialog.sort(key=lambda m: m["date"])

            results[name] = {"dialog": dialog}
        else:
            print(telegram_id)

    # Сохраняем всё в JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return output_path