from abc import ABC, abstractmethod
from typing import List, Dict
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class IntentProviderBase(ABC):
    def __init__(self, config):
        self.config = config

    def set_llm(self, llm):
        self.llm = llm
        # Get model name and type
        model_name = getattr(llm, "model_name", str(llm.__class__.__name__))
        # Log additional details
        logger.bind(tag=TAG).info(f"Intent detection LLM configured: {model_name}")

    @abstractmethod
    async def detect_intent(self, conn, dialogue_history: List[Dict], text: str) -> str:
        """
        Detect intent in the user's latest message
        Args:
            dialogue_history: Conversation history list; each item has role and content
        Returns:
            Return detected intent in formats such as:
            - "Continue chat"
            - "End chat"
            - "Play music: song title" or "Play random music"
            - "Check weather: location" or "Check weather: [current location]"
        """
        pass
