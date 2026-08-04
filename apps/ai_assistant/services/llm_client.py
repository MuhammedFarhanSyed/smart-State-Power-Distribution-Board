import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional
from apps.ai_assistant.services.fallback_service import FallbackService


class LLMClient:
    """
    Provider abstraction for external LLMs (OpenAI, Groq, Ollama, or Mock).
    Configured via environment variables:
      - AI_PROVIDER: 'openai' | 'groq' | 'ollama' | 'mock' (default: 'mock')
      - AI_API_KEY: Provider secret key
      - AI_MODEL: Target model identifier
    Falls back gracefully to FallbackService on any failure or missing key.
    """

    @classmethod
    def get_provider(cls) -> str:
        return os.getenv('AI_PROVIDER', 'mock').lower()

    @classmethod
    def get_api_key(cls) -> str:
        return os.getenv('AI_API_KEY', '')

    @classmethod
    def get_model(cls) -> str:
        provider = cls.get_provider()
        default_model = 'gpt-3.5-turbo' if provider == 'openai' else ('llama3-8b-8192' if provider == 'groq' else 'llama3')
        return os.getenv('AI_MODEL', default_model)

    @classmethod
    def generate_json_response(
        cls,
        system_prompt: str,
        user_prompt: str,
        fallback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Attempts to call the configured LLM provider to receive structured JSON.
        If provider is 'mock', unconfigured, or fails, returns fallback_data smoothly.
        """
        provider = cls.get_provider()
        api_key = cls.get_api_key()

        if provider == 'mock' or (provider in ['openai', 'groq'] and not api_key):
            return fallback_data

        try:
            if provider in ['openai', 'groq']:
                return cls._call_openai_compatible_api(provider, api_key, system_prompt, user_prompt, fallback_data)
            elif provider == 'ollama':
                return cls._call_ollama_api(system_prompt, user_prompt, fallback_data)
            else:
                return fallback_data
        except Exception:
            return fallback_data

    @classmethod
    def _call_openai_compatible_api(
        cls,
        provider: str,
        api_key: str,
        system_prompt: str,
        user_prompt: str,
        fallback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = "https://api.openai.com/v1/chat/completions" if provider == 'openai' else "https://api.groq.com/openai/v1/chat/completions"
        model = cls.get_model()

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')

        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            content = res_data['choices'][0]['message']['content']
            parsed = json.loads(content)
            parsed['is_fallback'] = False
            return parsed

    @classmethod
    def _call_ollama_api(
        cls,
        system_prompt: str,
        user_prompt: str,
        fallback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        url = os.getenv('OLLAMA_HOST', 'http://localhost:11434') + '/api/chat'
        model = cls.get_model()

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": "json",
            "stream": False
        }

        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')

        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            content = res_data['message']['content']
            parsed = json.loads(content)
            parsed['is_fallback'] = False
            return parsed
