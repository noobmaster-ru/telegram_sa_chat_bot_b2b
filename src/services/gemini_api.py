import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part, GenerationConfig
from google.genai import types

class GeminiVertexClient:
    def __init__(self, model_name: str, project_id: str, location: str = "us-central1"):
        # инициализация Vertex AI SDK
        vertexai.init(project=project_id, location=location)
        self.model = GenerativeModel(model_name)
        
    def create_text_request(self, prompt: str) -> str:
        """Отправляет текстовый запрос"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[ERROR] Ошибка при текстовом запросе: {e}")
            return None

    def create_image_request(self, prompt: str, image_path: str) -> str:
        """Отправляет текст + изображение"""
        try:

            image_bytes = open(image_path, "rb").read()
            image_part = Part.from_data(mime_type="image/jpeg", data=image_bytes)
            response = self.model.generate_content([prompt, image_part])
            return response.text
        except Exception as e:
            print(f"[ERROR] Ошибка при запросе с изображением: {e}")
            return None