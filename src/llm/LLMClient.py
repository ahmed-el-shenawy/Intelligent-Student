import openai
from typing import List
from helpers.config import settings

class LLMClient:
    def __init__(self, base_url, api_key, model_name):
        self.client = openai.OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model_name = model_name

    def response(self, prompt: str) -> str:
        instructions ="""You are a Educational chatbot. Follow these EXACT rules:

You are an Educational Chatbot. Follow these rules exactly:

1. You must answer only educational questions.
2. If the user asks a non-educational question, respond with: "I apologize, but I can only assist with Educational questions." in the same language the user used.
3. Your answers must rely only on the educational data you were provided.
4. Provide structured answers written in clear points.
5. Do not use * or ** symbols anywhere in your responses.
6. Automatically detect the user's language. If the user writes in Arabic, respond in Arabic; if in English, respond in English.
7. Maintain a professional, respectful tone at all times.
8. When asking "Would you like to hear the audio response?", use the same language the user is speaking.

# RESPONSE STRUCTURE:

1. Make the explanation easy for the user to follow.
2. Present the information in clear, organized points.
3. Ensure the structure encourages clear and effective learning.
4. Maintain a professional, consistent tone in every response.
5. Include a real-world example when it helps the user understand the concept more easily.
6. End the response with a short, clear conclusion that reinforces the main idea.

"""
        response = self.client.responses.create(
            model=self.model_name,
            instructions= instructions,
            input=prompt,
            # max_output_tokens=100  # limits the length
        )
        return response.output_text

    def embed(self, text: List[str]):
        embeddings = self.client.embeddings.create(
            model=self.model_name,
            input=text
        )
        return [item.embedding for item in embeddings.data]
