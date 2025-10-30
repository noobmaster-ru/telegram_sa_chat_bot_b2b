import re

class ToolsClass:
    @staticmethod
    def escape_markdown_v2(text: str) -> str:
        # Экранируем все специальные символы MarkdownV2
        escape_chars = r"_*[]()~`>#+-=|{}.!\\"
        return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)