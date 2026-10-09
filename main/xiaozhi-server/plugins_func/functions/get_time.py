from datetime import datetime
import cnlunar
from plugins_func.register import register_function, ToolType, ActionResponse, Action

get_lunar_function_desc = {
    "type": "function",
    "function": {
        "name": "get_lunar",
        "description": (
            "Look up lunar calendar and traditional almanac information for a specific date."
            "The user can request lunar dates, heavenly stems and earthly branches, solar terms, zodiac signs, eight characters, auspicious activities, and more."
            "If no topic is specified, return sexagenary year and lunar date."
            "For simple questions such as 'What is today's lunar date?', use context instead of calling this tool."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date to query, YYYY-MM-DD (e.g. 2024-01-01). Defaults to today.",
                },
                "query": {
                    "type": "string",
                    "description": "Requested topic, e.g. lunar date, stems and branches, festivals, solar terms, zodiac, eight characters, or auspicious activities",
                },
            },
            "required": [],
        },
    },
}


@register_function("get_lunar", get_lunar_function_desc, ToolType.WAIT)
def get_lunar(date=None, query=None):
    """
    Get the lunar date and traditional almanac information, including solar terms and zodiac
    """
    from core.utils.cache.manager import cache_manager, CacheType

    # Use supplied date if provided, otherwise today
    if date:
        try:
            now = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return ActionResponse(
                Action.REQLLM,
                f"Invalid date format. Use YYYY-MM-DD, for example 2024-01-01",
                None,
            )
    else:
        now = datetime.now()

    current_date = now.strftime("%Y-%m-%d")

    # Use default query when query is None
    if query is None:
        query = "Default query: sexagenary year and lunar date"

    # Try to load lunar data from cache
    lunar_cache_key = f"lunar_info_{current_date}"
    cached_lunar_info = cache_manager.get(CacheType.LUNAR, lunar_cache_key)
    if cached_lunar_info:
        return ActionResponse(Action.REQLLM, cached_lunar_info, None)

    response_text = f"Answer the user's query based on the following information and include details about {query}:\n"

    lunar = cnlunar.Lunar(now, godType="8char")
    response_text += (
        "Lunar calendar information:\n"
        "%syear%s%s\n" % (lunar.lunarYearCn, lunar.lunarMonthCn[:-1], lunar.lunarDayCn)
        + "Stems and branches: %syear %smonth %sday\n" % (lunar.year8Char, lunar.month8Char, lunar.day8Char)
        + "Chinese zodiac: Year of %s\n" % (lunar.chineseYearZodiac)
        + "Eight characters: %s\n"
        % (
            " ".join(
                [lunar.year8Char, lunar.month8Char, lunar.day8Char, lunar.twohour8Char]
            )
        )
        + "Today's festivals: %s\n"
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
        + "Today's solar term: %s\n" % (lunar.todaySolarTerms)
        + "Next solar term: %s %syear%smonth%sday\n"
        % (
            lunar.nextSolarTerm,
            lunar.nextSolarTermYear,
            lunar.nextSolarTermDate[0],
            lunar.nextSolarTermDate[1],
        )
        + "This year's solar terms: %s\n"
        % (
            ", ".join(
                [
                    f"{term}({date[0]}month{date[1]}day)"
                    for term, date in lunar.thisYearSolarTermsDic.items()
                ]
            )
        )
        + "Zodiac clashes: %s\n" % (lunar.chineseZodiacClash)
        + "Western zodiac: %s\n" % (lunar.starZodiac)
        + "Na Yin: %s\n" % lunar.get_nayin()
        + "Pengzu's taboos: %s\n" % (lunar.get_pengTaboo(delimit=", "))
        + "Day officer: %s officer\n" % lunar.get_today12DayOfficer()[0]
        + "Day deity: %s(%s)\n"
        % (lunar.get_today12DayOfficer()[1], lunar.get_today12DayOfficer()[2])
        + "Twenty-eight mansions: %s\n" % lunar.get_the28Stars()
        + "Auspicious directions: %s\n" % " ".join(lunar.get_luckyGodsDirection())
        + "Fetal spirit: %s\n" % lunar.get_fetalGod()
        + "Recommended: %s\n" % ", ".join(lunar.goodThing[:10])
        + "Avoid: %s\n" % ", ".join(lunar.badThing[:10])
        + "(Return the sexagenary year and lunar date by default; only include auspicious and inauspicious activities when requested.)"
    )

    # Cache lunar calendar information
    cache_manager.set(CacheType.LUNAR, lunar_cache_key, response_text)

    return ActionResponse(Action.REQLLM, response_text, None)
