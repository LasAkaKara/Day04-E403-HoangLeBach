from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def normalize_content(raw: Any) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        text = raw.get("text")
        return str(text).strip() if text is not None else str(raw).strip()
    if isinstance(raw, list):
        parts: list[str] = []
        for item in raw:
            text = normalize_content(item)
            if text:
                parts.append(text)
        return "\n".join(parts).strip()
    return str(raw).strip()


def _get_sleep_seconds(provider: str) -> float:
    env_value = os.getenv("LLM_CALL_SLEEP_SECONDS")
    if env_value is not None:
        try:
            return max(0.0, float(env_value))
        except ValueError:
            return 0.0
    provider_defaults = {
        "mistral": 1.0,
        "google": 0.0,
        "ollama": 0.0,
        "custom": 0.0,
    }
    return provider_defaults.get(provider, 0.0)


class ThrottledChatModel:
    def __init__(self, model: Any, *, sleep_seconds: float) -> None:
        self._model = model
        self._sleep_seconds = max(0.0, sleep_seconds)

    def _pause(self) -> None:
        if self._sleep_seconds > 0:
            time.sleep(self._sleep_seconds)

    def invoke(self, *args, **kwargs):
        self._pause()
        return self._model.invoke(*args, **kwargs)

    async def ainvoke(self, *args, **kwargs):
        self._pause()
        return await self._model.ainvoke(*args, **kwargs)

    def stream(self, *args, **kwargs):
        self._pause()
        yield from self._model.stream(*args, **kwargs)

    async def astream(self, *args, **kwargs):
        self._pause()
        async for chunk in self._model.astream(*args, **kwargs):
            yield chunk

    def bind_tools(self, *args, **kwargs):
        bound = self._model.bind_tools(*args, **kwargs)
        return ThrottledChatModel(bound, sleep_seconds=self._sleep_seconds)

    def with_structured_output(self, *args, **kwargs):
        structured = self._model.with_structured_output(*args, **kwargs)
        return ThrottledChatModel(structured, sleep_seconds=self._sleep_seconds)

    def with_config(self, *args, **kwargs):
        configured = self._model.with_config(*args, **kwargs)
        return ThrottledChatModel(configured, sleep_seconds=self._sleep_seconds)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._model, name)


def _wrap_model(model: Any, *, provider: str) -> Any:
    sleep_seconds = _get_sleep_seconds(provider)
    if sleep_seconds <= 0:
        return model
    return ThrottledChatModel(model, sleep_seconds=sleep_seconds)


def build_chat_model(
    *,
    provider: str = "google",
    model_name: str | None = None,
    temperature: float = 0.0,
):
    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI

        model = ChatGoogleGenerativeAI(
            model=model_name or os.getenv("LLM_MODEL", "gemini-2.5-flash"),
            temperature=temperature,
            google_api_key=os.getenv("GOOGLE_API_KEY"),
        )
        return _wrap_model(model, provider=provider)
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = ChatOllama(
            model=model_name or os.getenv("OLLAMA_MODEL", "qwen3.5:3b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=temperature,
        )
        return _wrap_model(model, provider=provider)
    if provider == "mistral":
        from langchain_mistralai import ChatMistralAI

        model = ChatMistralAI(
            model=model_name or os.getenv("MISTRAL_MODEL", "mistral-large-latest"),
            temperature=temperature,
            mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        )
        return _wrap_model(model, provider=provider)

    if provider == "custom":
        from langchain_openai import ChatOpenAI

        model = ChatOpenAI(
            model=model_name or os.getenv("CUSTOM_LLM_MODEL"),
            openai_api_key=os.getenv("CUSTOM_LLM_KEY"),
            openai_api_base=os.getenv("CUSTOM_LLM_URL"),
            temperature=temperature,
        )
        return _wrap_model(model, provider=provider)

    raise ValueError("This lab supports only the `google`, `ollama`, `mistral`, and `custom` providers.")



def extract_json_object(raw: Any) -> dict[str, Any]:
    text = normalize_content(raw)
    if "```" in text:
        blocks = re.findall(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
        if blocks:
            text = blocks[0].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output.")
    return json.loads(text[start : end + 1])


def judge_answer_with_llm(
    *,
    query: str,
    answer: str,
    rubric: str,
    provider: str,
    model_name: str | None = None,
) -> dict[str, Any]:
    model = build_chat_model(provider=provider, model_name=model_name, temperature=0.0)
    prompt = f"""
You are grading a student order-agent answer.
Return JSON only with:
- score: integer from 0 to 10
- verdict: short string
- feedback: short list of strings

Rubric:
{rubric}

User query:
{query}

Student answer:
{answer}
""".strip()
    payload = extract_json_object(model.invoke(prompt).content)
    score = max(0, min(10, int(payload.get("score", 0))))
    return {
        "score": score,
        "verdict": str(payload.get("verdict", "")).strip(),
        "feedback": [str(item).strip() for item in payload.get("feedback", []) if str(item).strip()],
    }
