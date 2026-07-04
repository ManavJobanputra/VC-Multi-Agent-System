import logging
import time
from typing import List, Dict, Optional
import requests
from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)


def _messages_to_gemini(messages: List[Dict]) -> Dict:
    """Convert OpenAI-style {role, content} messages into Gemini's
    {system_instruction, contents} request shape."""
    system_parts = []
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(content)
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": content}]})

    payload = {"contents": contents}
    if system_parts:
        payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
    return payload


def _extract_text(data: Dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = (candidates[0].get("content") or {}).get("parts") or []
    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()


class MistralClient:
    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.model = GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.session = requests.Session()

        masked_key = self.api_key[:4] + "..." + self.api_key[-4:] if len(self.api_key) > 8 else "****"
        logger.info(
            f"MistralClient (Gemini) initialized | model={self.model} | key={masked_key}"
        )

    def call_openrouter_api(
        self,
        messages: List[Dict],
        temperature: float = 0.1,
        max_tokens: int = 500,
        options: dict = None,
    ) -> str:
        """Calls Gemini's generateContent API.

        Name kept as call_openrouter_api for compatibility with existing
        agent call sites.
        """
        payload = _messages_to_gemini(messages)
        payload["generationConfig"] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {"thinkingBudget": 0},
        }
        if options:
            payload["generationConfig"].update(options)

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"

        for attempt in range(3):
            try:
                logger.info(f"[MistralClient] Gemini request attempt {attempt+1}")

                resp = self.session.post(url, json=payload, timeout=30)

                logger.info(f"[MistralClient] Status: {resp.status_code}")

                if resp.status_code != 200:
                    logger.error(
                        f"[MistralClient] Gemini API error: "
                        f"{resp.status_code} {resp.text}"
                    )
                    time.sleep(2 ** attempt)
                    continue

                result = _extract_text(resp.json())
                logger.info(
                    f"[MistralClient] Extracted content length: {len(result)}"
                )
                return result

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"[MistralClient] Network error "
                    f"(attempt {attempt+1}/3): {e}"
                )
                time.sleep(2 ** attempt)

            except Exception as e:
                logger.exception(
                    f"[MistralClient] Unexpected error: {e}"
                )
                break

        return ""

    def call_vision_api(
        self,
        image_base64: str,
        prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 200,
        model: Optional[str] = None,
    ) -> str:
        """Send image + prompt to a vision-capable Gemini model."""
        target_model = model or self.model
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": "image/png", "data": image_base64}},
                    ],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        url = f"{self.base_url}/{target_model}:generateContent?key={self.api_key}"

        for attempt in range(3):
            try:
                logger.info(f"[MistralClient] Vision request attempt {attempt+1}")

                resp = self.session.post(url, json=payload, timeout=60)

                logger.info(f"[MistralClient] Vision status: {resp.status_code}")

                if resp.status_code != 200:
                    logger.error(
                        f"[MistralClient] Vision API error: {resp.status_code} {resp.text}"
                    )
                    time.sleep(2 ** attempt)
                    continue

                result = _extract_text(resp.json())
                logger.info(
                    f"[MistralClient] Vision extracted content length: {len(result)}"
                )
                return result

            except requests.exceptions.RequestException as e:
                logger.error(
                    f"[MistralClient] Vision network error (attempt {attempt+1}/3): {e}"
                )
                time.sleep(2 ** attempt)

            except Exception as e:  # noqa: BLE001
                logger.exception(f"[MistralClient] Vision unexpected error: {e}")
                break

        return ""

    def close(self):
        self.session.close()
