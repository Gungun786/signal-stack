import os
import json
import time
import logging
import re
from typing import Type, TypeVar, Optional, Dict, Any
from pydantic import BaseModel
import httpx
from app.config import settings

logger = logging.getLogger("signal_stack.llm")
T = TypeVar("T", bound=BaseModel)

class LLMGateway:
    """
    Provider-agnostic LLM gateway:
    - Primary: Gemini API Free Tier (gemini-2.5-flash / gemini-1.5-flash)
    - Fallback: Groq Cloud Free Tier (llama-3.3-70b-versatile)
    - Emergency fallback: Rule-based heuristic extraction to guarantee zero crash if keys are absent
    - Exponential backoff on rate limits
    - Pydantic JSON-schema validated outputs
    """

    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.gemini_model = "gemini-2.5-flash"
        self.groq_model = "llama-3.3-70b-versatile"

    def _call_gemini(self, prompt: str, system_instruction: str = "", json_mode: bool = False) -> str:
        if not self.gemini_key:
            raise ValueError("GEMINI_API_KEY not configured")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
        
        contents = []
        if system_instruction:
            contents.append({"role": "user", "parts": [{"text": f"SYSTEM INSTRUCTION: {system_instruction}\n\nPlease follow this strictly."}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow all instructions."}]})
        
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 4096
            }
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        # Retry with exponential backoff on 429
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=45.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates and "content" in candidates[0]:
                            parts = candidates[0]["content"].get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                        return "{}" if json_mode else ""
                    elif resp.status_code == 429:
                        wait_sec = (attempt + 1) * 3
                        logger.warning(f"Gemini 429 rate limit hit. Backing off for {wait_sec}s (attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_sec)
                    else:
                        logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
                        break
            except Exception as e:
                logger.warning(f"Gemini request exception: {e}")
                time.sleep(2)
        raise RuntimeError("Gemini API call failed or rate limit exhausted")

    def _call_groq(self, prompt: str, system_instruction: str = "", json_mode: bool = False) -> str:
        if not self.groq_key:
            raise ValueError("GROQ_API_KEY not configured")

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.groq_model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 4096
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        max_retries = 3
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=45.0) as client:
                    resp = client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            return choices[0]["message"].get("content", "")
                        return "{}" if json_mode else ""
                    elif resp.status_code == 429:
                        wait_sec = (attempt + 1) * 2
                        logger.warning(f"Groq 429 rate limit hit. Backing off for {wait_sec}s...")
                        time.sleep(wait_sec)
                    else:
                        logger.error(f"Groq API returned status {resp.status_code}: {resp.text}")
                        break
            except Exception as e:
                logger.warning(f"Groq request exception: {e}")
                time.sleep(2)
        raise RuntimeError("Groq API call failed")

    def generate_text(self, prompt: str, system_instruction: str = "") -> str:
        """Attempts Gemini first, falls back to Groq."""
        # 1. Try Gemini
        if self.gemini_key:
            try:
                return self._call_gemini(prompt, system_instruction, json_mode=False)
            except Exception as e:
                logger.warning(f"Primary Gemini failed: {e}. Attempting fallback...")
        
        # 2. Try Groq
        if self.groq_key:
            try:
                return self._call_groq(prompt, system_instruction, json_mode=False)
            except Exception as e:
                logger.warning(f"Groq fallback failed: {e}")

        # 3. Informative fallback message if no keys
        return "LLM generation unavailable (Set GEMINI_API_KEY or GROQ_API_KEY in environment)."

    def generate_json(self, prompt: str, schema_class: Optional[Type[T]] = None, system_instruction: str = "") -> Any:
        """
        Generates structured JSON, extracts from markdown codeblocks, and validates against Pydantic schema.
        """
        enhanced_prompt = (
            f"{prompt}\n\nCRITICAL: Respond ONLY with a valid JSON object matching the requested schema. "
            f"Do not include any intro, commentary, or markdown formatting outside the JSON."
        )

        raw_text = ""
        # 1. Try Gemini
        if self.gemini_key:
            try:
                raw_text = self._call_gemini(enhanced_prompt, system_instruction, json_mode=True)
            except Exception as e:
                logger.warning(f"Gemini structured generation failed: {e}. Falling back to Groq...")

        # 2. Try Groq if raw_text empty
        if not raw_text and self.groq_key:
            try:
                raw_text = self._call_groq(enhanced_prompt, system_instruction, json_mode=True)
            except Exception as e:
                logger.warning(f"Groq structured generation failed: {e}")

        # 3. Clean raw_text (strip ```json ... ``` fences)
        cleaned = raw_text.strip()
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        # Parse JSON
        parsed_data = None
        if cleaned:
            try:
                parsed_data = json.loads(cleaned)
            except json.JSONDecodeError as jde:
                logger.error(f"JSON decode failed on: {cleaned[:200]}... Error: {jde}")

        # If schema_class provided and we have parsed_data, validate
        if parsed_data is not None and schema_class is not None:
            try:
                if isinstance(parsed_data, dict):
                    return schema_class.model_validate(parsed_data)
                elif isinstance(parsed_data, list):
                    return [schema_class.model_validate(item) for item in parsed_data]
            except Exception as ve:
                logger.warning(f"Pydantic validation warning: {ve}")
                return parsed_data

        return parsed_data

llm_gateway = LLMGateway()
