
from .provider_base import LLMProvider

class LocalLLMProvider(LLMProvider):

    def complete(self, prompt):
        return "Local LLM suggestion for: " + prompt
