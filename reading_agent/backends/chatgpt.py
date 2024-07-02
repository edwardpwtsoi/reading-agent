import datetime
import logging
import os
import time
from typing import Tuple

import openai
from openai.types.chat import ChatCompletion

from reading_agent.backends.base import BackendBase

logger = logging.getLogger(__name__)


class GPTBackend(BackendBase):
    def __init__(self, temperature: float = 0.0, max_decode_steps: int = 512,
                 seconds_to_reset_tokens: float = 30.0, **kwargs):
        super().__init__(**kwargs)
        self.deployment = os.environ["GPT_DEPLOYMENT_NAME"]
        self.temperature = temperature
        self.max_decode_steps = max_decode_steps
        self.seconds_to_reset_tokens = seconds_to_reset_tokens
        self.client = openai.AzureOpenAI(
            azure_endpoint=os.environ["GPT_ENDPOINT"],
            api_key=os.environ["GPT_API_KEY"],
            api_version=os.environ["GPT_API_VERSION"],
        )

    def query_model(self, prompt: str, **kwargs) -> Tuple[int, str]:
        while True:
            try:
                raw_response = self.client.chat.completions.with_raw_response.create(
                    model=self.deployment,
                    max_tokens=self.max_decode_steps,
                    temperature=self.temperature,
                    messages=[
                        {'role': 'user', 'content': prompt},
                    ]
                )
                completion: ChatCompletion = raw_response.parse()
                return completion.usage.total_tokens, completion.choices[0].message.content
            except (openai.RateLimitError, openai.Timeout) as e:
                logger.warning(f'{datetime.datetime.now()}: query_gpt_model: {type(e)} {e.message}: {e}')
                logger.error(f'{datetime.datetime.now()}: query_gpt_model: Retrying after {self.seconds_to_reset_tokens} seconds...')
                time.sleep(self.seconds_to_reset_tokens)
            except openai.APIError as e:
                logger.error(f'{datetime.datetime.now()}: query_gpt_model: APIError {e.message}: {e}')
                raise
