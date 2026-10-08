from datetime import datetime
import cnlunar
from plugins_func.register import register_function, ToolType, ActionResponse, Action

get_lunar_function_desc = {
    "type": "function",
    "function": {
        "name": "get_lunar",
        "description": (
            "Provide Chinese lunar calendar and almanac information for a given date."
            "The user may ask about lunar dates, heavenly stems/earthly branches, solar terms, zodiac, constellations, Four Pillars, and auspicious activities."
            "If no specific query is given, return the lunar date and year cycle."
            "For a simple question about today's lunar date, use the date already in system context; do not call this tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format (e.g. 2024-01-01); default is today",
                },
                "query": {
                    "type": "string",
                    "description": "Requested details, such as lunar date, solar terms, zodiac or auspicious activities",
                },
            },
            "required": [],
        },
    },
}


@register_function("get_lunar", get_lunar_function_desc, ToolType.WAIT)
def get_lunar(date=None, query=None):
    """
    Return Chinese lunar calendar and almanac information, including zodiac and auspicious activities
    """
    from core.utils.cache.manager import cache_manager, CacheType

    # Use provided date or the current date
    if date:
        try:
            now = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return ActionResponse(
                Action.REQLLM,
                f"Invalid date. Use YYYY-MM-DD, for example 2024-01-01",
                None,
            )
    else:
        now = datetime.now()

    current_date = now.strftime("%Y-%m-%d")

    # Use a default description when query is None
    if query is None:
        query = "Lunar date and year cycle"

    # Attempt to get lunar data from cache
    lunar_cache_key = f"lunar_info_{current_date}"
    cached_lunar_info = cache_manager.get(CacheType.LUNAR, lunar_cache_key)
    if cached_lunar_info:
        return ActionResponse(Action.REQLLM, cached_lunar_info, None)

    response_text = f"Use the following information to answer the user's question about {query}. Translate Chinese calendar names into the user's requested language:\n"

    lunar = cnlunar.Lunar(now, godType="8char")
    response_text += (
        "Lunar calendar:\n"
        "%s year, %s%s\n" % (lunar.lunarYearCn, lunar.lunarMonthCn[:-1], lunar.lunarDayCn)
        + "Heavenly stems and earthly branches: year %s, month %s, day %s\n" % (lunar.year8Char, lunar.month8Char, lunar.day8Char)
        + "Chinese zodiac: %s\n" % (lunar.chineseYearZodiac)
        + "Four Pillars (Ba Zi): %s\n"
        % (
            " ".join(
                [lunar.year8Char, lunar.month8Char, lunar.day8Char, lunar.twohour8Char]
            )
        )
        + "Holidays today: %s\n"
        % (
            ",".join(
                filter(
                    None,
                    (
                        lunar.get_legalHolidays(),
                        lunar.get_otherHolidays(),
                        lunar.get_otherLunarHolidays(),
                    ),
                )
            )
        )
        + "Current solar term: %s\n" % (lunar.todaySolarTerms)
        + "Next solar term: %s, %s-%s-%s\n"
        % (
            lunar.nextSolarTerm,
            lunar.nextSolarTermYear,
            lunar.nextSolarTermDate[0],
            lunar.nextSolarTermDate[1],
        )
        + "Solar terms this year: %s\n"
        % (
            ", ".join(
                [
                    f"{term}({date[0]}/{date[1]})"
                    for term, date in lunar.thisYearSolarTermsDic.items()
                ]
            )
        )
        + "Zodiac clash: %s\n" % (lunar.chineseZodiacClash)
        + "Western zodiac: %s\n" % (lunar.starZodiac)
        + "Na Yin element: %s\n" % lunar.get_nayin()
        + "Peng Zu taboos: %s\n" % (lunar.get_pengTaboo(delimit=", "))
        + "Day officer: %s\n" % lunar.get_today12DayOfficer()[0]
        + "Day deity: %s (%s)\n"
        % (lunar.get_today12DayOfficer()[1], lunar.get_today12DayOfficer()[2])
        + "Twenty-eight lunar mansions: %s\n" % lunar.get_the28Stars()
        + "Auspicious directions: %s\n" % " ".join(lunar.get_luckyGodsDirection())
        + "Fetal deity: %s\n" % lunar.get_fetalGod()
        + "Recommended activities: %s\n" % ", ".join(lunar.goodThing[:10])
        + "Activities to avoid: %s\n" % ", ".join(lunar.badThing[:10])
        + "(By default, focus on the lunar date and year cycle; include auspicious activities only when requested)"
    )

    # Cache lunar information
    cache_manager.set(CacheType.LUNAR, lunar_cache_key, response_text)

    return ActionResponse(Action.REQLLM, response_text, None)
