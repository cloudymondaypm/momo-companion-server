import httpx
from bs4 import BeautifulSoup
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from core.utils.util import get_ip_info
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

GET_WEATHER_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": (
            "Get weather for a named location. For 'What's the weather in Hangzhou?', use location='Hangzhou'. "
            "For province-level or vague locations, use the corresponding capital city when necessary. "
            "The user's local seven-day forecast is already in the context. Do not call this tool unless the user specifies another location."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Location, such as Hangzhou; optional",
                },
                "lang": {
                    "type": "string",
                    "description": "Language code, e.g. en_US, zh_CN, zh_HK, ja_JP. Default: en_US.",
                },
            },
            "required": ["lang"],
        },
    },
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
    )
}

# Weather condition codes https://dev.qweather.com/docs/resource/icons/#weather-icons
WEATHER_CODE_MAP = {
    "100": "Sunny",
    "101": "Cloudy",
    "102": "Mostly clear",
    "103": "Partly cloudy",
    "104": "Overcast",
    "150": "Sunny",
    "151": "Cloudy",
    "152": "Mostly clear",
    "153": "Partly cloudy",
    "300": "Showers",
    "301": "Heavy showers",
    "302": "Thunderstorms",
    "303": "Severe thunderstorms",
    "304": "Thunderstorms with hail",
    "305": "Light rain",
    "306": "Moderate rain",
    "307": "Heavy rain",
    "308": "Extreme rainfall",
    "309": "Drizzle",
    "310": "Torrential rain",
    "311": "Very heavy rain",
    "312": "Extreme torrential rain",
    "313": "Freezing rain",
    "314": "Light to moderate rain",
    "315": "Moderate to heavy rain",
    "316": "Heavy to torrential rain",
    "317": "Torrential to very heavy rain",
    "318": "Very heavy to extreme torrential rain",
    "350": "Showers",
    "351": "Heavy showers",
    "399": "Rain",
    "400": "Light snow",
    "401": "Moderate snow",
    "402": "Heavy snow",
    "403": "Snowstorm",
    "404": "Sleet",
    "405": "Mixed rain and snow",
    "406": "Snow and rain showers",
    "407": "Snow showers",
    "408": "Light to moderate snow",
    "409": "Moderate to heavy snow",
    "410": "Heavy snow to snowstorm",
    "456": "Snow and rain showers",
    "457": "Snow showers",
    "499": "Snow",
    "500": "Mist",
    "501": "Fog",
    "502": "Haze",
    "503": "Blowing sand",
    "504": "Dust",
    "507": "Sandstorm",
    "508": "Severe sandstorm",
    "509": "Dense fog",
    "510": "Very dense fog",
    "511": "Moderate haze",
    "512": "Heavy haze",
    "513": "Severe haze",
    "514": "Thick fog",
    "515": "Extremely dense fog",
    "900": "Hot",
    "901": "Cold",
    "999": "Unknown",
}


async def fetch_city_info(location, api_key, api_host):
    url = f"https://{api_host}/geo/v2/city/lookup?key={api_key}&location={location}&lang=zh"
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
        response = await client.get(url, headers=HEADERS)
    data = response.json()
    if data.get("error") is not None:
        logger.bind(tag=TAG).error(
            f"Failed to retrieve weather data; reason：{data.get('error', {}).get('detail')}"
        )
        return None
    return data.get("location", [])[0] if data.get("location") else None


async def fetch_weather_page(url):
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
        response = await client.get(url, headers=HEADERS)
    return BeautifulSoup(response.text, "html.parser") if response.status_code == 200 else None


def parse_weather_info(soup):
    city_name = soup.select_one("h1.c-submenu__location").get_text(strip=True)

    current_abstract = soup.select_one(".c-city-weather-current .current-abstract")
    current_abstract = (
        current_abstract.get_text(strip=True) if current_abstract else "Unknown"
    )

    current_basic = {}
    for item in soup.select(
        ".c-city-weather-current .current-basic .current-basic___item"
    ):
        parts = item.get_text(strip=True, separator=" ").split(" ")
        if len(parts) == 2:
            key, value = parts[1], parts[0]
            current_basic[key] = value

    temps_list = []
    for row in soup.select(".city-forecast-tabs__row")[:7]:  # Use seven-day forecast
        date = row.select_one(".date-bg .date").get_text(strip=True)
        weather_code = (
            row.select_one(".date-bg .icon")["src"].split("/")[-1].split(".")[0]
        )
        weather = WEATHER_CODE_MAP.get(weather_code, "Unknown")
        temps = [span.get_text(strip=True) for span in row.select(".tmp-cont .temp")]
        high_temp, low_temp = (temps[0], temps[-1]) if len(temps) >= 2 else (None, None)
        temps_list.append((date, weather, high_temp, low_temp))

    return city_name, current_abstract, current_basic, temps_list


@register_function("get_weather", GET_WEATHER_FUNCTION_DESC, ToolType.SYSTEM_CTL)
async def get_weather(conn: "ConnectionHandler", location: str = None, lang: str = "en_US"):
    from core.utils.cache.manager import cache_manager, CacheType

    weather_config = conn.config.get("plugins", {}).get("get_weather", {})
    api_host = weather_config.get("api_host", "mj7p3y7naa.re.qweatherapi.com")
    api_key = weather_config.get("api_key", "a861d0d5e7bf4ee1a83d9a9e4f96d4da")
    default_location = weather_config.get("default_location", "Guangzhou")
    client_ip = conn.client_ip

    # Prefer an explicit user location
    if not location:
        # Look up city from client IP
        if client_ip:
            # Check cached IP location first
            cached_ip_info = cache_manager.get(CacheType.IP_INFO, client_ip)
            if cached_ip_info:
                location = cached_ip_info.get("city")
            else:
                # Cache miss; query API
                ip_info = get_ip_info(client_ip, logger)
                if ip_info:
                    cache_manager.set(CacheType.IP_INFO, client_ip, ip_info)
                    location = ip_info.get("city")

            if not location:
                location = default_location
        else:
            # Default to configured location when client IP is unavailable
            location = default_location
    # Read full weather report from cache
    weather_cache_key = f"full_weather_{location}_{lang}"
    cached_weather_report = cache_manager.get(CacheType.WEATHER, weather_cache_key)
    if cached_weather_report:
        return ActionResponse(Action.REQLLM, cached_weather_report, None)

    # Cache miss; fetch live weather data
    city_info = await fetch_city_info(location, api_key, api_host)
    if not city_info:
        return ActionResponse(
            Action.REQLLM, f"City not found: {location}. Check the location.", None
        )
    soup = await fetch_weather_page(city_info["fxLink"])
    if not soup:
        return ActionResponse(Action.REQLLM, None, "Request failed")
    city_name, current_abstract, current_basic, temps_list = parse_weather_info(soup)

    weather_report = f"Location: {city_name}\n\nCurrent weather: {current_abstract}\n"

    # Add valid current conditions
    if current_basic:
        weather_report += "Details:\n"
        for key, value in current_basic.items():
            if value != "0":  # Ignore invalid values
                weather_report += f"  · {key}: {value}\n"

    # Add seven-day forecast
    weather_report += "\nNext seven days:\n"
    for date, weather, high, low in temps_list:
        weather_report += f"{date}: {weather}; temperature {low}~{high}\n"

    # Follow-up prompt
    weather_report += "\n(Ask for a specific date if you want more details.)"

    # Cache full weather report
    cache_manager.set(CacheType.WEATHER, weather_cache_key, weather_report)

    return ActionResponse(Action.REQLLM, weather_report, None)
