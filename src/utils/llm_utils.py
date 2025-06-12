import json
import re

import requests
from loguru import logger
from requests.exceptions import HTTPError, Timeout, ReadTimeout
from tenacity import stop_after_attempt, retry, wait_random, wait_fixed
from urllib3.exceptions import ReadTimeoutError

from src.lib.config import LLM_BASE_URL, LLM_MODEL, LLM_API_VERSION, LLM_API_KEY
from src.lib.enums import Language

url = f"{LLM_BASE_URL}/openai/deployments/{LLM_MODEL}/chat/completions?api-version={LLM_API_VERSION}"
headers = {"Content-Type": "application/json", "api-key": LLM_API_KEY}


@retry(wait=wait_random(3, 7), stop=stop_after_attempt(3), reraise=True)
def llm_translate_vtt(vtt_content: str, language: Language) -> str:
    data = {
        "messages": [
            {"role": "system", "content": "You are a subtitle translator."},
            {"role": "user", "content": f"""Translate the following VTT subtitle content into {language.long_code}, while strictly preserving the original WebVTT format. 

Instructions:
- Do NOT change the timestamps.
- Do NOT translate or remove formatting tags like <i>, <b>, <c>, etc.
- ONLY translate the spoken text.
- Keep line breaks and structure exactly as they are.
- Do NOT return any explanations, headers, footers, or comments.
- Do NOT wrap the response in triple backticks or any code block.
- ONLY return the translated VTT content as plain text.

Input:
{vtt_content}"""}
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        response_message = response.json()["choices"][0]["message"]
        if 'content' not in response_message:
            logger.error(f"LLM translation failed, {str(response_message)}")
            return ""

        return response.json()["choices"][0]["message"]["content"]
    except HTTPError as e:
        # due to the prompt triggering Azure OpenAI's content management policy.
        if e.response.status_code == 400 and e.response.reason == "Bad Request":
            return ""
        else:
            raise
    except (Timeout, ReadTimeoutError, ReadTimeout) as e:
        return ""


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def translate_video_content(content: dict, language: Language) -> dict:
    data = {
        "messages": [
            {"role": "system", "content": "You are a video content translator."},
            {"role": "user", "content": f"""Translate the following video content into {language.long_code}. 

Input Content:
Title: {content['title']}
Description: {content['description']}
Tags: {', '.join(content['tags'])}
Categories: {', '.join(content['categories'])}

Instructions:
- Translate all content naturally and fluently
- Keep special characters and numbers unchanged
- For tags and categories, translate each item and keep them as a list
- Return a valid JSON object without any explanations, wrapper, headers, footers, or comments.
- The return JSON structure should be:
{{
    "title": "<translated title>",
    "description": "<translated description>",
    "tags": ["<translated tag 1>", "<translated tag 2>", ...],
    "categories": ["<translated category 1>", "<translated category 2>", ...]
}}
"""}
        ],
        "temperature": 0.5
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    cleaned = remove_code_block_wrapper(content)
    return json.loads(cleaned)


def remove_code_block_wrapper(text):
    if not text.strip():
        return text
    return re.sub(r'^```\w*\n|\n```$', '', text.strip())
