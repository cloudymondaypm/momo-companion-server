from ..base import IntentProviderBase
from typing import List, Dict
from config.logger import setup_logging

TAG = __name__
logger = setup_logging()


class IntentProvider(IntentProviderBase):
    async def detect_intent(self, conn, dialogue_history: List[Dict], text: str) -> str:
        """
        Default intent implementation; always continues chat
        Args:
            dialogue_history: Conversation history list
            text: Current message
        Returns:
            Always return continue_chat
        """
        logger.bind(tag=TAG).debug(
            "Using NoIntentProvider, always returning continue chat"
        )
        return '{"function_call": {"name": "continue_chat"}}'
