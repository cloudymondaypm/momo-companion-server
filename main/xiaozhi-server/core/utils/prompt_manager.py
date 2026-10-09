"""
System prompt manager module
Manages and updates system prompts, including fast initialization and asynchronous enrichment
"""

import os
import asyncio
import threading
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler
from config.logger import setup_logging
from jinja2 import Template

TAG = __name__

WEEKDAY_MAP = {
    "Monday": "Monday",
    "Tuesday": "Tuesday",
    "Wednesday": "Wednesday",
    "Thursday": "Thursday",
    "Friday": "Friday",
    "Saturday": "Saturday",
    "Sunday": "Sunday",
}

EMOJI_List = [
    "😶",
    "🙂",
    "😆",
    "😂",
    "😔",
    "😠",
    "😭",
    "😍",
    "😳",
    "😲",
    "😱",
    "🤔",
    "😉",
    "😎",
    "😌",
    "🤤",
    "😘",
    "😏",
    "😴",
    "😜",
    "🙄",
]


class PromptManager:
    """System prompt manager for updating and enriching prompts"""

    def __init__(self, config: Dict[str, Any], logger=None):
        self.config = config
        self.logger = logger or setup_logging()
        self.base_prompt_template = None
        self.last_update_time = 0

        # Import global cache manager
        from core.utils.cache.manager import cache_manager, CacheType

        self.cache_manager = cache_manager
        self.CacheType = CacheType

        # Initialize context provider
        from core.utils.context_provider import ContextDataProvider

        self.context_provider = ContextDataProvider(config, self.logger)
        self.context_data = {}

        self._load_base_template()

    def _load_base_template(self):
        """Load base prompt template"""
        try:
            template_path = self.config.get("prompt_template", None)
            if not template_path:
                template_path = "agent-base-prompt.txt"
            cache_key = f"prompt_template:{template_path}"

            # Check cache first
            cached_template = self.cache_manager.get(self.CacheType.CONFIG, cache_key)
            if cached_template is not None:
                self.base_prompt_template = cached_template
                self.logger.bind(tag=TAG).debug("Loaded base prompt template from cache")
                return

            # On cache miss, read file
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    template_content = f.read()

                # Cache it (CONFIG entries do not expire automatically; invalidate manually)
                self.cache_manager.set(
                    self.CacheType.CONFIG, cache_key, template_content
                )
                self.base_prompt_template = template_content
                self.logger.bind(tag=TAG).debug("Loaded and cached base prompt template")
            else:
                self.logger.bind(tag=TAG).warning(f"Template file not found: {template_path}")
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to load prompt template: {e}")

    def get_quick_prompt(self, user_prompt: str, device_id: str = None) -> str:
        """Get system prompt quickly using user configuration"""
        device_cache_key = f"device_prompt:{device_id}"
        cached_device_prompt = self.cache_manager.get(
            self.CacheType.DEVICE_PROMPT, device_cache_key
        )
        if cached_device_prompt is not None:
            self.logger.bind(tag=TAG).debug(f"Using cached prompt for device {device_id}")
            return cached_device_prompt
        else:
            self.logger.bind(tag=TAG).debug(
                f"No cached prompt for device {device_id}; using supplied prompt"
            )

        # Use supplied prompt and cache it if device ID is available
        if device_id:
            device_cache_key = f"device_prompt:{device_id}"
            self.cache_manager.set(self.CacheType.DEVICE_PROMPT, device_cache_key, user_prompt)
            self.logger.bind(tag=TAG).debug(f"Cached prompt for device {device_id}")

        self.logger.bind(tag=TAG).info(f"Using fast prompt: {user_prompt[:50]}...")
        return user_prompt

    def _get_current_time_info(self) -> tuple:
        """Get current time information"""
        from .current_time import (
            get_current_date,
            get_current_weekday,
            get_current_lunar_date,
        )

        today_date = get_current_date()
        today_weekday = get_current_weekday()
        lunar_date = get_current_lunar_date() + "\n"

        return today_date, today_weekday, lunar_date

    def _get_location_info(self, client_ip: str) -> str:
        """Get location information"""
        try:
            # Check cache first
            cached_location = self.cache_manager.get(self.CacheType.LOCATION, client_ip)
            if cached_location is not None:
                return cached_location

            # On cache miss, call API
            from core.utils.util import get_ip_info

            ip_info = get_ip_info(client_ip, self.logger)
            city = ip_info.get("city", "Unknown location")
            location = f"{city}"

            # Write to cache
            self.cache_manager.set(self.CacheType.LOCATION, client_ip, location)
            return location
        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to get location: {e}")
            return "Unknown location"

    def _get_weather_info(self, conn: "ConnectionHandler", location: str) -> str:
        """Get weather information"""
        try:
            # Check cache first
            cached_weather = self.cache_manager.get(self.CacheType.WEATHER, location)
            if cached_weather is not None:
                return cached_weather

            # On cache miss, call async get_weather
            # Windows ProactorEventLoop does not support run_coroutine_threadsafe().result()
            # Use call_soon_threadsafe to schedule task, then threading.Event to wait
            # Note: Event.wait() blocks the worker thread, not main event loop
            from plugins_func.functions.get_weather import get_weather
            from plugins_func.register import ActionResponse

            result_holder = []
            exception_holder = []

            async def _call():
                try:
                    result_holder.append(
                        await get_weather(conn, location=location, lang="zh_CN")
                    )
                except Exception as e:
                    exception_holder.append(e)
                finally:
                    event.set()

            event = threading.Event()
            conn.loop.call_soon_threadsafe(lambda: asyncio.ensure_future(_call()))
            if not event.wait(timeout=10):
                raise TimeoutError("Timed out retrieving weather")
            if exception_holder:
                raise exception_holder[0]
            result = result_holder[0]
            if isinstance(result, ActionResponse):
                weather_report = result.result
                self.cache_manager.set(self.CacheType.WEATHER, location, weather_report)
                return weather_report
            return "Failed to retrieve weather"

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to retrieve weather: {e}")
            return "Failed to retrieve weather"

    def update_context_info(self, conn, client_ip: str):
        """Update context information synchronously"""
        try:
            local_address = ""
            if (
                client_ip
                and self.base_prompt_template
                and (
                    "local_address" in self.base_prompt_template
                    or "weather_info" in self.base_prompt_template
                )
            ):
                # Get location using global cache
                local_address = self._get_location_info(client_ip)

            if (
                self.base_prompt_template
                and "weather_info" in self.base_prompt_template
                and local_address
            ):
                # Get weather using global cache
                self._get_weather_info(conn, local_address)

            # Get configured context data
            if hasattr(conn, "device_id") and conn.device_id:
                if (
                    self.base_prompt_template
                    and "dynamic_context" in self.base_prompt_template
                ):
                    self.context_data = self.context_provider.fetch_all(conn.device_id)
                else:
                    self.context_data = ""

            self.logger.bind(tag=TAG).debug(f"Context information updated")

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to update context information: {e}")

    def build_enhanced_prompt(
        self, user_prompt: str, device_id: str, client_ip: str = None, *args, **kwargs
    ) -> str:
        """Build enriched system prompt"""
        if not self.base_prompt_template:
            return user_prompt

        try:
            # Get latest time without caching
            today_date, today_weekday, lunar_date = self._get_current_time_info()

            # Get cached context information
            local_address = ""
            weather_info = ""

            if client_ip:
                # Get location from global cache
                local_address = (
                    self.cache_manager.get(self.CacheType.LOCATION, client_ip) or ""
                )

                # Get weather from global cache
                if local_address:
                    weather_info = (
                        self.cache_manager.get(self.CacheType.WEATHER, local_address)
                        or ""
                    )

            # Get selected TTS language, default English
            language = (
                self.config.get("TTS", {})
                .get(self.config.get("selected_module", {}).get("TTS", ""), {})
                .get("language")
                or "English"
            )
            self.logger.bind(tag=TAG).debug(f"Selected language: {language}")

            # Render template variables
            template = Template(self.base_prompt_template)
            enhanced_prompt = template.render(
                base_prompt=user_prompt,
                current_time="{{current_time}}",
                today_date=today_date,
                today_weekday=today_weekday,
                lunar_date=lunar_date,
                local_address=local_address,
                weather_info=weather_info,
                emojiList=EMOJI_List,
                device_id=device_id,
                client_ip=client_ip,
                dynamic_context=self.context_data,
                language=language,
                *args,
                **kwargs,
            )
            device_cache_key = f"device_prompt:{device_id}"
            self.cache_manager.set(
                self.CacheType.DEVICE_PROMPT, device_cache_key, enhanced_prompt
            )
            self.logger.bind(tag=TAG).info(
                f"Built enriched prompt, length: {len(enhanced_prompt)}"
            )
            return enhanced_prompt

        except Exception as e:
            self.logger.bind(tag=TAG).error(f"Failed to build enriched prompt: {e}")
            return user_prompt
