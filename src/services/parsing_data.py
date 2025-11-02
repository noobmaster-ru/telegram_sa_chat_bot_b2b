import json
from pathlib import Path
import aiofiles
import logging

class ParsingDataClass:
    @staticmethod
    async def parse_telegram_export_async(json_path: str, seller_telegram_id: int, output_path: str = "parsed_data.json") -> Path:
        """
        Асинхронно парсит Telegram export result.json файл и сохраняет диалоги в parsed_data.json.
        Возвращает путь к результату.
        """
        # --- читаем json ---
        async with aiofiles.open(json_path, "r", encoding="utf-8") as f:
            raw_data = await f.read()
            data = json.loads(raw_data)

        chats = data.get("chats", {}).get("list", [])
        results = {}
        skip_telegram_id = [777000, 547299317, 694144143]

        for chat in chats:
            name = chat.get("name") or chat.get("title") or "Unknown"
            telegram_id = chat.get("id")
            type_ = chat.get("type")

            # фильтруем только личные чаты, не системные
            if (telegram_id not in skip_telegram_id) and type_ == "personal_chat":
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

                    sender_label = "me" if sender == "Ты" else sender

                    dialog.append({
                        "from": sender_label,
                        "text": text,
                        "date": date
                    })

                results[name] = {"dialog": dialog}

        # --- сохраняем результат ---
        async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(results, ensure_ascii=False, indent=2))

        logging.info(f"✅ parsed  data from {seller_telegram_id} to {output_path}")
        return Path(output_path)