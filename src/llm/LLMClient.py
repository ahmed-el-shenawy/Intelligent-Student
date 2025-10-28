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
        instructions="""Answer the question based on the context.
          Keep the response concise short .
            if the user query was not a qestion ask him/her what do you mean .
            if the context was meaningless for answering the query say that i don't know"""
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
