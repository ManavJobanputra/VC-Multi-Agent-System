import logging
import time
from typing import List, Dict, Optional
import requests
from config import OPENROUTER_API_KEY, MISTRAL_MODEL

logger = logging.getLogger(__name__)


class MistralClient:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.model = MISTRAL_MODEL
        self.openrouter_url = "https://openrouter.ai/api/v1"
        self.session = requests.Session()

        masked_key = self.api_key[:4] + "..." + self.api_key[-4:]
        logger.info(
            f"MistralClient initialized | model={self.model} | key={masked_key}"
        )

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def call_openrouter_api(
        self,
        messages: List[Dict],
        temperature: float = 0.1,
        max_tokens: int = 500,
        options: dict = None,
    ) -> str:
        """
        EXACT same OpenRouter usage pattern as LLMBrain
        """

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if options:
            payload.update(options)

        url = f"{self.openrouter_url}/chat/completions"

        for attempt in range(3):
            try:
                logger.info(f"[MistralClient] OpenRouter request attempt {attempt+1}")

                resp = self.session.post(
                    url,
                    json=payload,
                    headers=self._headers(),
                    timeout=30,
                )

                logger.info(f"[MistralClient] Status: {resp.status_code}")

                if resp.status_code != 200:
                    logger.error(
                        f"[MistralClient] OpenRouter API error: "
                        f"{resp.status_code} {resp.text}"
                    )
                    time.sleep(2 ** attempt)
                    continue

                data = resp.json()

                # 🔒 SAME parsing logic as LLMBrain
                choice = (data.get("choices") or [{}])[0]
                message = choice.get("message") or {}

                if isinstance(message, dict):
                    content = message.get("content") or ""
                else:
                    content = choice.get("text") or ""

                result = (content or "").strip()
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
        """Send image + prompt to a vision-capable OpenRouter model (hardcoded config)."""

        payload = {
            "model": model or self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                        },
                    ],
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        url = f"{self.openrouter_url}/chat/completions"

        for attempt in range(3):
            try:
                logger.info(f"[MistralClient] Vision request attempt {attempt+1}")

                resp = self.session.post(
                    url,
                    json=payload,
                    headers=self._headers(),
                    timeout=60,
                )

                logger.info(f"[MistralClient] Vision status: {resp.status_code}")

                if resp.status_code != 200:
                    logger.error(
                        f"[MistralClient] Vision API error: {resp.status_code} {resp.text}"
                    )
                    time.sleep(2 ** attempt)
                    continue

                data = resp.json()
                choice = (data.get("choices") or [{}])[0]
                message = choice.get("message") or {}

                if isinstance(message, dict):
                    content = message.get("content") or ""
                else:
                    content = choice.get("text") or ""

                result = (content or "").strip()
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
