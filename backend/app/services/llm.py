import asyncio
import json
import re
from openai import AsyncOpenAI
from pydantic import ValidationError
from app.config import get_settings
from app.services.prompts.condensing_prompt import CONDENSING_PROMPT
from app.services.prompts.range_system_prompt import RANGE_SYSTEM_PROMPT, CHAPTER_RANGES_SCHEMA, RANGE_JSON_INSTRUCTION
from app.services.prompts.range_user_prompt import RANGE_USER_PROMPT
from app.services.app_models.chunk_models import ChapterRangesFormat
from app.exceptions.validation import InputTooLargeError, MAX_INPUT_CHARS


MODEL = "deepseek/deepseek-v4-flash"
MAX_PARSE_RETRIES = 3

_settings = get_settings()

client = AsyncOpenAI(base_url=_settings.base_url, api_key=_settings.llm_api_key)


def _extract_and_parse(raw: str) -> ChapterRangesFormat:
    text = raw.strip()
    # Remove ```json ... ``` or ``` ... ``` fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()
    data = json.loads(text)
    return ChapterRangesFormat(**data)

def create_text_chunk_list(text: str) -> list:

    character_threshold_per_line = 30_000
    stripped_text = text.strip()
    text_lines = stripped_text.split("\n")
    threshold_check = any(len(line) > character_threshold_per_line for line in text_lines)
    chunk_list = []
    if threshold_check:

        sentence = re.split(r'(?=[.!?…])\s*', stripped_text)
        for idx, i in enumerate(sentence):
            chunk_list.append({"chunk_id": idx, "chunk": i})

    for idx, line in enumerate(text_lines):
        chunk_list.append({"chunk_id": idx, "chunk": line})

    return chunk_list

async def validate_chapter_ranges(chunks: list, counter: int = 0, tokens: int = 0) -> list:

    tasks = [chapter_ranges_with_llm(chunks) for _ in range(3)]

    results = await asyncio.gather(*tasks)


    if results[0]["chapter_ranges"] == results[1]["chapter_ranges"] or results[0]["chapter_ranges"] == results[2]["chapter_ranges"]:
        results[0]["tokens_in"] += results[1]["tokens_in"] + results[2]["tokens_in"]
        results[0]["tokens_out"] += results[1]["tokens_out"] + results[2]["tokens_out"]
        return results[0]
    elif results[1]["chapter_ranges"] == results[2]["chapter_ranges"]:
        results[1]["tokens_in"] += results[0]["tokens_in"] + results[0]["tokens_in"]
        results[1]["tokens_out"] += results[0]["tokens_out"] + results[0]["tokens_out"]
        return results[1]
    else:
        if counter > 3:
            raise Exception("LLM is not providing consistent chapter ranges after multiple attempts.")

        tokens_counter = sum([result["tokens_in"] + result["tokens_out"] for result in results])
        return await validate_chapter_ranges(chunks, counter + 1, tokens + tokens_counter)


async def chapter_ranges_with_llm(chunks: list) -> dict:

    messages = [
        {"role": "system", "content": RANGE_SYSTEM_PROMPT + RANGE_JSON_INSTRUCTION},
        {"role": "user", "content": RANGE_USER_PROMPT.format(chunks=chunks)},
    ]

    total_tokens_in = 0
    total_tokens_out = 0
    last_error: Exception = None

    for _ in range(1, MAX_PARSE_RETRIES + 1):
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )

        raw = response.choices[0].message.content
        usage = response.usage
        total_tokens_in += usage.prompt_tokens
        total_tokens_out += usage.completion_tokens

        try:
            parsed = _extract_and_parse(raw)
            return {
                "chapter_ranges": parsed,
                "tokens_in": total_tokens_in,
                "tokens_out": total_tokens_out,
            }
        except (json.JSONDecodeError, ValidationError, TypeError, KeyError) as e:
            last_error = e

            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": (
                    f"Your response could not be parsed. Error: {e}\n"
                    "Please reply with ONLY valid JSON — no markdown, no explanation, "
                    f"exactly matching this structure:\n{CHAPTER_RANGES_SCHEMA}"
                ),
            })

    raise ValueError(
        f"Failed to parse a valid chapter ranges response after {MAX_PARSE_RETRIES} attempts. "
        f"Last error: {last_error}"
    )

def chapters_from_ranges(chunks: list, chapter_ranges: list) -> list:

    chapters = []

    for chapter in chapter_ranges:
        start = chapter.start
        end = chapter.end

        print(f"Processing chapter range: start={start}, end={end}")

        chapter_chunks = [chunk for chunk in chunks if int(chunk["chunk_id"]) >= start and int(chunk["chunk_id"]) <= end]
        chapter_text = " ".join([chunk["chunk"] for chunk in chapter_chunks])

        chapter_info = {
            "text": chapter_text,
            "chapter_number": chapter.chapter_number,
            "chapter_title": chapter.chapter_title
        }
        chapters.append(chapter_info)

    return chapters

async def condense_chapters(text: str, chapter_info: dict = None) -> dict:
    chapter_header = ""
    if chapter_info:
        if chapter_info.get('chapter_number'):
            chapter_header += f"Chapter {chapter_info['chapter_number']}"
        if chapter_info.get('chapter_title'):
            if chapter_header:
                chapter_header += f": {chapter_info['chapter_title']}"
            else:
                chapter_header += chapter_info['chapter_title']
        if chapter_header:
            chapter_header += "\n\n"

    formatted_prompt = CONDENSING_PROMPT.format(chunk=text)
    messages = [{"role": "user", "content": formatted_prompt}]

    total_tokens_in = 0
    total_tokens_out = 0
    last_error: Exception = None

    for _ in range(1, MAX_PARSE_RETRIES + 1):
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
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

        finish_reason = response.choices[0].finish_reason if response.choices else "no_choices"
        last_error = ValueError(f"Empty content in response (finish_reason: {finish_reason})")

        messages.append({"role": "assistant", "content": ""})
        messages.append({"role": "user", "content": "Please provide the condensed text."})

    raise ValueError(
        f"Failed to get a text response after {MAX_PARSE_RETRIES} attempts. "
        f"Last error: {last_error}"
    )
async def condense_with_llm(text: str) -> dict:

    if len(text) > MAX_INPUT_CHARS:
        raise InputTooLargeError(
            log_message=f"Input text exceeds maximum allowed characters ({MAX_INPUT_CHARS}). Actual length: {len(text)}"
        )

    chunks = create_text_chunk_list(text)
    chapter_ranges_result = await chapter_ranges_with_llm(chunks)


    chapter_ranges_list = chapter_ranges_result["chapter_ranges"]
    if hasattr(chapter_ranges_list, 'chapter_ranges'):

        chapter_ranges_list = chapter_ranges_list.chapter_ranges

    chapters = chapters_from_ranges(chunks, chapter_ranges_list)

    condensed_chapters = await asyncio.gather(*[condense_chapters(chapter["text"], {"chapter_number": chapter["chapter_number"], "chapter_title": chapter["chapter_title"]}) for chapter in chapters])

    final_text = "\n\n".join([chapter["condensed"] for chapter in condensed_chapters])
    return {
        "text": final_text,
        "condensed_chapters": condensed_chapters,
        "tokens_in": chapter_ranges_result["tokens_in"] + sum([chapter["tokens_in"] for chapter in condensed_chapters]),
        "tokens_out": chapter_ranges_result["tokens_out"] + sum([chapter["tokens_out"] for chapter in condensed_chapters]),
        }






