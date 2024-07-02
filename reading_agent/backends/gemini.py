import logging
import os

import google.generativeai as genai

from reading_agent.backends.base import BackendBase

logger = logging.getLogger(__name__)


class GeminiBackend(BackendBase):
    def __init__(self):
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self.client = genai.GenerativeModel('gemini-pro')

    def query_gemini_model(
            self,
            prompt: str,
            retries: int = 10,
    ) -> str:
        while retries > 0:
            try:
                response = self.client.generate_content(prompt)
                text_response = response.text.replace("**", "")
                return text_response
            except Exception as e:
                logger.error(f'Error: {e}')
                logger.error('Retrying after 5 seconds...')
                retries -= 1
