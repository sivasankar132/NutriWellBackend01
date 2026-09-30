import json
import re
import urllib.request
import urllib.error
import socket
from typing import Dict, Any, Type, TypeVar, Optional
from pydantic import BaseModel, ValidationError
from app.core.config import settings
from app.utils.error_handlers import AIContractException

T = TypeVar("T", bound=BaseModel)

class GeminiService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = "gemini-flash-lite-latest"

    def _get_api_key(self, custom_key: Optional[str] = None) -> str:
        key = custom_key or self.api_key
        if not key or not key.strip():
            raise AIContractException(
                error_code="GEMINI_UNAUTHORIZED",
                message="AI generation failed. Please try again.",
                status_code=401
            )
        return key.strip()

    def _call_gemini_raw(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_mime_type: str = "image/jpeg",
        custom_key: Optional[str] = None,
        timeout: int = 15
    ) -> str:
        api_key = self._get_api_key(custom_key)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={api_key}"

        parts = []
        if system_instruction:
            parts.append({"text": f"SYSTEM INSTRUCTION:\n{system_instruction}\n\nUSER PROMPT:\n{prompt}"})
        else:
            parts.append({"text": prompt})

        if image_base64:
            clean_b64 = image_base64.split(",")[1] if "," in image_base64 else image_base64
            parts.append({
                "inline_data": {
                    "mime_type": image_mime_type,
                    "data": clean_b64
                }
            })

        payload = {
            "contents": [
                {
                    "parts": parts
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))
                candidates = resp_body.get("candidates", [])
                if not candidates:
                    raise AIContractException(
                        error_code="GEMINI_INVALID_RESPONSE",
                        message="AI generation failed. Please try again.",
                        status_code=502
                    )
                
                parts_out = candidates[0].get("content", {}).get("parts", [])
                if not parts_out or not parts_out[0].get("text"):
                    raise AIContractException(
                        error_code="GEMINI_INVALID_RESPONSE",
                        message="AI generation failed. Please try again.",
                        status_code=502
                    )

                return parts_out[0].get("text", "").strip()

        except urllib.error.HTTPError as he:
            if he.code in (401, 403):
                raise AIContractException(
                    error_code="GEMINI_UNAUTHORIZED",
                    message="AI generation failed. Please try again.",
                    status_code=he.code
                )
            elif he.code == 429:
                raise AIContractException(
                    error_code="GEMINI_RATE_LIMITED",
                    message="AI generation failed. Please try again.",
                    status_code=429
                )
            else:
                raise AIContractException(
                    error_code="GEMINI_UNAVAILABLE",
                    message="AI generation failed. Please try again.",
                    status_code=502
                )
        except (urllib.error.URLError, socket.timeout, TimeoutError):
            raise AIContractException(
                error_code="GEMINI_TIMEOUT",
                message="AI generation failed. Please try again.",
                status_code=504
            )
        except AIContractException as ace:
            raise ace
        except Exception:
            raise AIContractException(
                error_code="GEMINI_UNAVAILABLE",
                message="AI generation failed. Please try again.",
                status_code=502
            )

    def _extract_json_string(self, text: str) -> str:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        start_dict = text.find("{")
        start_arr = text.find("[")

        if start_dict != -1 and (start_arr == -1 or start_dict < start_arr):
            end_dict = text.rfind("}")
            if end_dict != -1:
                return text[start_dict:end_dict+1]
        elif start_arr != -1:
            end_arr = text.rfind("]")
            if end_arr != -1:
                return text[start_arr:end_arr+1]

        return text

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_instruction: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_mime_type: str = "image/jpeg",
        custom_key: Optional[str] = None
    ) -> T:
        raw_text = self._call_gemini_raw(
            prompt=prompt,
            system_instruction=system_instruction,
            image_base64=image_base64,
            image_mime_type=image_mime_type,
            custom_key=custom_key
        )

        clean_json = self._extract_json_string(raw_text)
        if not clean_json:
            raise AIContractException(
                error_code="GEMINI_INVALID_JSON",
                message="AI generation failed. Please try again.",
                status_code=502
            )

        try:
            parsed_data = json.loads(clean_json)
        except Exception:
            # Fix trailing comma issues or single quote formatting if any
            try:
                fixed_json = re.sub(r",\s*([\]}])", r"\1", clean_json)
                parsed_data = json.loads(fixed_json)
            except Exception:
                raise AIContractException(
                    error_code="GEMINI_INVALID_JSON",
                    message="AI generation failed. Please try again.",
                    status_code=502
                )

        try:
            validated_obj = schema.model_validate(parsed_data)
            return validated_obj
        except ValidationError:
            raise AIContractException(
                error_code="GEMINI_SCHEMA_VALIDATION_FAILED",
                message="AI generation failed. Please try again.",
                status_code=502
            )

gemini_service = GeminiService()
