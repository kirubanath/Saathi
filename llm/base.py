from abc import ABC, abstractmethod
from config.settings import settings


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, system: str = None) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_json(self, prompt: str, system: str = None, schema: dict = None) -> dict:
        raise NotImplementedError


def get_llm_client() -> LLMClient:
    if settings.ENVIRONMENT == "prototype":
        from llm.anthropic_client import AnthropicClient
        return AnthropicClient()
    raise NotImplementedError(f"No LLM client for environment: {settings.ENVIRONMENT}")
