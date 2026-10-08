import random
import httpx
from io import BytesIO
from markitdown import MarkItDown, StreamInfo
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler


TAG = __name__
logger = setup_logging()

CHANNEL_MAP = {
    "V2EX": "v2ex-share",
    "知乎": "zhihu",
    "微博": "weibo",
    "联合早报": "zaobao",
    "酷安": "coolapk",
    "MKTNews": "mktnews-flash",
    "华尔街见闻": "wallstreetcn-quick",
    "36氪": "36kr-quick",
    "抖音": "douyin",
    "虎扑": "hupu",
    "百度贴吧": "tieba",
    "今日头条": "toutiao",
    "IT之家": "ithome",
    "澎湃新闻": "thepaper",
    "卫星通讯社": "sputniknewscn",
    "参考消息": "cankaoxiaoxi",
    "远景论坛": "pcbeta-windows11",
    "财联社": "cls-depth",
    "雪球": "xueqiu-hotstock",
    "格隆汇": "gelonghui",
    "法布财经": "fastbull-express",
    "Solidot": "solidot",
    "Hacker News": "hackernews",
    "Product Hunt": "producthunt",
    "Github": "github-trending-today",
    "哔哩哔哩": "bilibili-hot-search",
    "快手": "kuaishou",
    "靠谱新闻": "kaopu",
    "金十数据": "jin10",
    "百度热搜": "baidu",
    "牛客": "nowcoder",
    "少数派": "sspai",
    "稀土掘金": "juejin",
    "凤凰网": "ifeng",
    "虫部落": "chongbuluo-latest",
}

# Default source names when no configuration is provided
DEFAULT_NEWS_SOURCES = "澎湃新闻;百度热搜;财联社"

def _get_newsnow_config(conn):
    # Get from connection settings
    plugins = conn.config.get("plugins", {})
    newsnow = plugins.get("get_news_from_newsnow", {})
    sources = newsnow.get("news_sources", "")
    if isinstance(sources, str) and sources.strip():
        return sources

    return ""

def get_news_sources_from_config(conn):
    """Read configured news source names"""
    try:
        result = _get_newsnow_config(conn)
        if result:
            logger.bind(tag=TAG).debug(f"Using configured news sources: {result}")
            return result

        logger.bind(tag=TAG).debug("No news sources configured; using defaults")
        return DEFAULT_NEWS_SOURCES

    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to read news source configuration: {e}; using defaults")
        return DEFAULT_NEWS_SOURCES


# Fetch available news sources from defaults (resolved dynamically)
example_sources_str = DEFAULT_NEWS_SOURCES.replace(";","、")

GET_NEWS_FROM_NEWSNOW_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_news_from_newsnow",
        "description": "Call when the user asks for current news or headlines.",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": f"Exact provider identifier from the configured news sources, e.g. {example_sources_str}. Optional; default provider if omitted.",
                },
                "detail": {
                    "type": "boolean",
                    "description": "Whether to get the previously mentioned article's details. Default: false.",
                },
                "lang": {
                    "type": "string",
                    "description": "Response language code (en_US, zh_CN, ja_JP etc.); default en_US.",
                },
            },
            "required": ["lang"],
        },
    },
}


async def fetch_news_from_api(conn: "ConnectionHandler", source="thepaper"):
    """Fetch news items from API"""
    try:
        api_url = f"https://newsnow.busiyi.world/api/s?id={source}"

        news_config = conn.config.get("plugins", {}).get("get_news_from_newsnow", {})
        if news_config.get("url"):
            api_url = news_config["url"] + source

        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            response = await client.get(api_url, headers=headers)

        data = response.json()

        if "items" in data:
            return data["items"]
        else:
            logger.bind(tag=TAG).error(f"Malformed news API response: {data}")
            return []

    except Exception as e:
        logger.bind(tag=TAG).error(f"News API request failed: {e}")
        return []


async def fetch_news_detail(url):
    """Get article details and clean HTML using MarkItDown"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            response = await client.get(url, headers=headers)

        # Clean HTML using MarkItDown
        md = MarkItDown(enable_plugins=False)
        result = md.convert_stream(
            BytesIO(response.content),
            stream_info=StreamInfo(
                mimetype="text/html",
                extension=".html",
                charset=response.encoding or "utf-8",
            ),
        )

        # Read cleaned article text
        clean_text = result.text_content

        # Return an error when cleaned article text is empty
        if not clean_text or len(clean_text.strip()) == 0:
            logger.bind(tag=TAG).warning(f"Cleaned article content is empty: {url}")
            return "Unable to parse article details; the site structure or access restrictions may prevent extraction."

        return clean_text
    except Exception as e:
        logger.bind(tag=TAG).error(f"Unable to fetch article details: {e}")
        return "Unable to retrieve article details"


@register_function(
    "get_news_from_newsnow",
    GET_NEWS_FROM_NEWSNOW_FUNCTION_DESC,
    ToolType.SYSTEM_CTL,
)
async def get_news_from_newsnow(
    conn: "ConnectionHandler",
    source: str = "澎湃新闻",
    detail: bool = False,
    lang: str = "en_US",
):
    """Get a random news item or details about the previous item"""
    try:
        # Get available configured news sources
        news_sources = get_news_sources_from_config(conn)

        # If detail is true, get the previous article's details
        detail = str(detail).lower() == "true"
        if detail:
            if (
                not hasattr(conn, "last_newsnow_link")
                or not conn.last_newsnow_link
                or "url" not in conn.last_newsnow_link
            ):
                return ActionResponse(
                    Action.REQLLM,
                    "There is no previous news story. Ask me for a headline first.",
                    None,
                )

            url = conn.last_newsnow_link.get("url")
            title = conn.last_newsnow_link.get("title", "Unknown title")
            source_id = conn.last_newsnow_link.get("source_id", "thepaper")
            source_name = CHANNEL_MAP.get(source_id, "Unknown source")

            if not url or url == "#":
                return ActionResponse(
                    Action.REQLLM, "Sorry, this article does not have a link for more details.", None
                )

            logger.bind(tag=TAG).debug(
                f"Getting news details: {title}, 来源: {source_name}, URL={url}"
            )

            # Getting news details
            detail_content = await fetch_news_detail(url)

            if not detail_content or detail_content == "Unable to retrieve article details":
                return ActionResponse(
                    Action.REQLLM,
                    f"Sorry, I could not retrieve details for {title}; the link may have expired or the page format changed.",
                    None,
                )

            # Build detail report
            detail_report = (
                f"Respond to the user's news detail request in {lang} using:\n\n"
                f"Headline: {title}\n"
                # f"News source: {source_name}\n"
                f"Article details: {detail_content}\n\n"
                f"(Summarize the key facts in natural, fluent spoken language. "
                f"Do not mention summarization; tell it as a complete story.)"
            )

            return ActionResponse(Action.REQLLM, detail_report, None)

        # Otherwise, fetch a list and select a random story
        # Map source name to API provider ID
        english_source_id = None

        # Validate source against configured providers
        news_sources_list = [
            name.strip() for name in news_sources.split(";") if name.strip()
        ]
        if source in news_sources_list:
            # Look up the provider ID in CHANNEL_MAP
            english_source_id = CHANNEL_MAP.get(source)

        # Fall back to default provider ID
        if not english_source_id:
            logger.bind(tag=TAG).warning(f"Invalid news source: {source}; using The Paper")
            english_source_id = "thepaper"
            source = "澎湃新闻"

        logger.bind(tag=TAG).info(f"Getting news from source={source}({english_source_id})")

        # Get news list
        news_items = await fetch_news_from_api(conn, english_source_id)

        if not news_items:
            return ActionResponse(
                Action.REQLLM,
                f"Sorry, no news was available from {source}. Try again or choose another provider.",
                None,
            )

        # Choose a random article
        selected_news = random.choice(news_items)

        # Save current article for follow-up queries
        if not hasattr(conn, "last_newsnow_link"):
            conn.last_newsnow_link = {}
        conn.last_newsnow_link = {
            "url": selected_news.get("url", "#"),
            "title": selected_news.get("title", "Unknown title"),
            "source_id": english_source_id,
        }

        # Build news report
        news_report = (
            f"Respond to the user's news request in {lang} using:\n\n"
            f"Headline: {selected_news['title']}\n"
            # f"News source: {source}\n"
            f"(Read the headline naturally and fluently. "
            f"Mention that the user can request the full article details.)"
        )

        return ActionResponse(Action.REQLLM, news_report, None)

    except Exception as e:
        logger.bind(tag=TAG).error(f"Error retrieving news: {e}")
        return ActionResponse(
            Action.REQLLM, "Sorry, there was an error retrieving news. Please try again later.", None
        )
