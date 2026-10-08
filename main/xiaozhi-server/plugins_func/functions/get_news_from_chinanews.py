import random
import httpx
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler


TAG = __name__
logger = setup_logging()

GET_NEWS_FROM_CHINANEWS_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "get_news_from_chinanews",
        "description": (
            "Call when a user requests current news, such as 'Read the news' or 'What's in the news today?'."
            "The user can specify a news category, such as society, technology, world, or finance."
            "Default to society news when no category is specified."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "News category such as society, technology, world, or finance. Optional.",
                },
                "detail": {
                    "type": "boolean",
                    "description": "Whether to request full details for the last news item. Default: false.",
                },
                "lang": {
                    "type": "string",
                    "description": "Response language code (e.g. en_US, zh_CN, ja_JP); default en_US.",
                },
            },
            "required": ["lang"],
        },
    },
}


async def fetch_news_from_rss(rss_url):
    """Read news items from RSS feed"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as client:
            response = await client.get(rss_url)

        # Parse XML
        root = ET.fromstring(response.content)

        # Find all RSS item elements
        news_items = []
        for item in root.findall(".//item"):
            title = (
                item.find("title").text if item.find("title") is not None else "Untitled"
            )
            link = item.find("link").text if item.find("link") is not None else "#"
            description = (
                item.find("description").text
                if item.find("description") is not None
                else "No description"
            )
            pubDate = (
                item.find("pubDate").text
                if item.find("pubDate") is not None
                else "Unknown date"
            )

            news_items.append(
                {
                    "title": title,
                    "link": link,
                    "description": description,
                    "pubDate": pubDate,
                }
            )

        return news_items
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to fetch RSS news: {e}")
        return []


async def fetch_news_detail(url):
    """Read news article content for summarization"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=3.0)) as client:
            response = await client.get(url)

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract main article content (adjust selectors for each site)
        content_div = soup.select_one(
            ".content_desc, .content, article, .article-content"
        )
        if content_div:
            paragraphs = content_div.find_all("p")
            content = "\n".join(
                [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            )
            return content
        else:
            # Fall back to extracting all paragraphs
            paragraphs = soup.find_all("p")
            content = "\n".join(
                [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
            )
            return content[:2000]  # Limit content length
    except Exception as e:
        logger.bind(tag=TAG).error(f"Failed to fetch article details: {e}")
        return "Unable to retrieve article details"


def map_category(category_text):
    """Map English or Chinese category name to the corresponding RSS setting"""
    if not category_text:
        return None

    # Category aliases for society, world, and finance; extend via configuration
    category_map = {
        "society": "society_rss_url",
        "social": "society_rss_url",
        "world": "world_rss_url",
        "international": "world_rss_url",
        "finance": "finance_rss_url",
        "financial": "finance_rss_url",
        "economy": "finance_rss_url",
        # Society news
        "社会": "society_rss_url",
        "society news": "society_rss_url",
        "社会新闻": "society_rss_url",
        # World news
        "国际": "world_rss_url",
        "world news": "world_rss_url",
        "国际新闻": "world_rss_url",
        # Finance news
        "财经": "finance_rss_url",
        "finance news": "finance_rss_url",
        "财经新闻": "finance_rss_url",
        "金融": "finance_rss_url",
        "经济": "finance_rss_url",
    }

    # Normalize case and remove surrounding whitespace
    normalized_category = category_text.lower().strip()

    # Return mapped category or original value
    return category_map.get(normalized_category, category_text)


@register_function(
    "get_news_from_chinanews",
    GET_NEWS_FROM_CHINANEWS_FUNCTION_DESC,
    ToolType.SYSTEM_CTL,
)
async def get_news_from_chinanews(
    conn: "ConnectionHandler",
    category: str = None,
    detail: bool = False,
    lang: str = "en_US",
):
    """Get a random news item, or details about the last one"""
    try:
        # If detail is true, retrieve the last article
        if detail:
            if (
                not hasattr(conn, "last_news_link")
                or not conn.last_news_link
                or "link" not in conn.last_news_link
            ):
                return ActionResponse(
                    Action.REQLLM,
                    "I don't have a previous news story yet. Ask me for the latest news first.",
                    None,
                )

            link = conn.last_news_link.get("link")
            title = conn.last_news_link.get("title", "Unknown title")

            if link == "#":
                return ActionResponse(
                    Action.REQLLM, "Sorry, that article doesn't have a link for more details.", None
                )

            logger.bind(tag=TAG).debug(f"Fetching news details: {title}, URL={link}")

            # Fetching news details
            detail_content = await fetch_news_detail(link)

            if not detail_content or detail_content == "Unable to retrieve article details":
                return ActionResponse(
                    Action.REQLLM,
                    f"Sorry, I couldn't retrieve details for {title}. The link may have expired or the page layout changed.",
                    None,
                )

            # Build article details report
            detail_report = (
                f"Answer the user's request for news details in {lang}, using the following data:\n\n"
                f"Headline: {title}\n"
                f"Article details: {detail_content}\n\n"
                f"(Summarize the key facts naturally and clearly for spoken delivery. "
                f"Do not announce that this is a summary; tell it like a complete news story.)"
            )

            return ActionResponse(Action.REQLLM, detail_report, None)

        # Otherwise, retrieve RSS items and choose one
        # Read RSS URL from configuration
        rss_config = conn.config.get("plugins", {}).get("get_news_from_chinanews", {})
        default_rss_url = rss_config.get(
            "default_rss_url", "https://www.chinanews.com.cn/rss/society.xml"
        )

        # Map requested category to configured RSS key
        mapped_category = map_category(category)

        # Look up category-specific URL when provided
        rss_url = default_rss_url
        if mapped_category and mapped_category in rss_config:
            rss_url = rss_config[mapped_category]

        logger.bind(tag=TAG).info(
            f"Fetching news: input category={category}, mapped category={mapped_category}, URL={rss_url}"
        )

        # Fetch news list
        news_items = await fetch_news_from_rss(rss_url)

        if not news_items:
            return ActionResponse(
                Action.REQLLM, "Sorry, I couldn't load the news. Please try again later.", None
            )

        # Choose a random news item
        selected_news = random.choice(news_items)

        # Save article URL for follow-up detail requests
        if not hasattr(conn, "last_news_link"):
            conn.last_news_link = {}
        conn.last_news_link = {
            "link": selected_news.get("link", "#"),
            "title": selected_news.get("title", "Unknown title"),
        }

        # Build news report
        news_report = (
            f"Answer the user's news request in {lang} using this information:\n\n"
            f"Headline: {selected_news['title']}\n"
            f"Published: {selected_news['pubDate']}\n"
            f"News content: {selected_news['description']}\n"
            f"(Read the story in a natural, fluent speaking style. Summarize when appropriate. "
            f"Avoid unnecessary introduction or filler. "
            f"If asked for more details, explain that the user can ask 'Tell me more about this story'.)"
        )

        return ActionResponse(Action.REQLLM, news_report, None)

    except Exception as e:
        logger.bind(tag=TAG).error(f"Error retrieving news: {e}")
        return ActionResponse(
            Action.REQLLM, "Sorry, there was an error retrieving the news. Please try again.", None
        )
