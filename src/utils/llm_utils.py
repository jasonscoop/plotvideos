import json

import requests
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.config import LLM_BASE_URL, LLM_MODEL, LLM_API_VERSION, LLM_API_KEY
from src.lib.consts import BigLanguage


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def translate_vtt(vtt_content: str, language: BigLanguage) -> str:
    url = f"{LLM_BASE_URL}/openai/deployments/{LLM_MODEL}/chat/completions?api-version={LLM_API_VERSION}"

    headers = {
        "Content-Type": "application/json",
        "api-key": LLM_API_KEY
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are a subtitle translator."},
            {"role": "user", "content": f"""Translate the following VTT subtitle content into {language.full_name}, while strictly preserving the original WebVTT format. 

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

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    return content


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def translate_title(title: str, language: BigLanguage) -> str:
    url = f"{LLM_BASE_URL}/openai/deployments/{LLM_MODEL}/chat/completions?api-version={LLM_API_VERSION}"

    headers = {
        "Content-Type": "application/json",
        "api-key": LLM_API_KEY
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are a title translator."},
            {"role": "user", "content": f"""Translate the following title into {language.full_name}. 
            
Instructions:
- Preserve any numbers or special characters
- Keep the translation natural and fluent
- Do NOT add any explanations or comments
- Return ONLY the translated title

Title: {title}"""}
        ],
        "temperature": 0.5
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    return content.strip()


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def translate_video_content(content: dict, language: BigLanguage) -> dict:
    """
    Translate all video content (title, description, tags, categories) at once.
    
    Args:
        content: dict containing title, description, tags, and categories
        language: target language
    """
    url = f"{LLM_BASE_URL}/openai/deployments/{LLM_MODEL}/chat/completions?api-version={LLM_API_VERSION}"

    headers = {
        "Content-Type": "application/json",
        "api-key": LLM_API_KEY
    }

    data = {
        "messages": [
            {"role": "system", "content": "You are a video content translator."},
            {"role": "user", "content": f"""Translate the following video content into {language.full_name}. 
            Return the result in a JSON format.

Input Content:
Title: {content['title']}
Description: {content['description']}
Tags: {', '.join(content['tags'])}
Categories: {', '.join(content['categories'])}

Instructions:
- Translate all content naturally and fluently
- Keep special characters and numbers unchanged
- For tags and categories, translate each item and keep them as a list
- Return ONLY a valid JSON object with the following structure:
{{
    "title": "<translated title>",
    "description": "<translated description>",
    "tags": ["<translated tag 1>", "<translated tag 2>", ...],
    "categories": ["<translated category 1>", "<translated category 2>", ...]
}}"""}
        ],
        "temperature": 0.5
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    return json.loads(content.strip())
