from abc import ABC, abstractmethod
import json

from pydantic_core import ValidationError

from pydantic_core import ValidationError
from app.utils.model_constants import FALLBACK_MODELS, MODEL


MAX_RETRIES = 4
class LLMFunction(ABC):
    @abstractmethod
    def get_response(self, *args, **kwargs):
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if "get_response" not in cls.__dict__:
            raise TypeError(
                f"Class '{cls.__name__}' failed because 'get_response' method is not present."
            )

class condense_chapters_function(LLMFunction):
    def __init__(self, client, prompt):
        self.client = client
        self.prompt = prompt


    async def get_response(self) -> dict:


        total_tokens_in = 0
        total_tokens_out = 0

        for _ in range(1, MAX_RETRIES):
            response = await self.client.chat.completions.create(
                model=MODEL,
                extra_body={
                    "models": FALLBACK_MODELS,

                },
                messages=self.prompt,
            )

            usage = response.usage
            total_tokens_in += usage.prompt_tokens
            total_tokens_out += usage.completion_tokens

            content = response.choices[0].message.content if response.choices else None

            if content:
                return {
                    "condensed": content,
                    "tokens_in": total_tokens_in,
                    "tokens_out": total_tokens_out,
                }

        raise Exception("Failed to get a valid response after maximum retries")

class chapter_ranges_function(LLMFunction):
    def __init__(self, client, prompt, extract_and_parse):
        self.client = client
        self.prompt = prompt
        self.extract_and_parse = extract_and_parse
        self.max_retries = 4

    async def get_response(self) -> dict:


        total_tokens_in = 0
        total_tokens_out = 0

        for _ in range(1, MAX_RETRIES):
            response = await self.client.chat.completions.create(
                model=MODEL,
                extra_body={
                    "models": FALLBACK_MODELS,
                },
                messages=self.prompt,
            )

            raw = response.choices[0].message.content
            usage = response.usage
            total_tokens_in += usage.prompt_tokens
            total_tokens_out += usage.completion_tokens

            try:
                parsed = self.extract_and_parse(raw)
                return {
                    "chapter_ranges": parsed,
                    "tokens_in": total_tokens_in,
                    "tokens_out": total_tokens_out,
                }
            except (json.JSONDecodeError, ValidationError, TypeError, KeyError) as e:
                last_error = e

                self.prompt.append({"role": "assistant", "content": raw})
                self.prompt.append({
                    "role": "user",
                    "content": (
                        f"Your response could not be parsed. Error: {e}\n"
                        "Please reply with ONLY valid JSON — no markdown, no explanation, "
                        f"exactly matching this structure:\n{CHAPTER_RANGES_SCHEMA}"
                    ),
                })
        raise ValueError(
            f"Failed to parse a valid chapter ranges response after {self.max_retries} attempts. "
            f"Last error: {last_error}")

