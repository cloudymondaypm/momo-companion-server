# Momo Companion: English Localization Status

This document tracks the staged localization of the upstream Xiaozhi server and Momo Companion interfaces.

## Scope

English should be the default user-facing language for the management web console, mobile console, digital-human interface, server messages, plugin descriptions, and documentation. Preserve non-English language support.

## Implemented on this branch

- English default and fallback language settings in the web and mobile consoles.
- English API message properties and many hardcoded management API messages.
- English documentation: deployment guides, firmware/OTA, MQTT, Home Assistant, MCP, RAGFlow, voice cloning, wake words, and other integrations.
- English labels, dialogs, status messages, tools, and error handling in the browser-based digital-human UI.
- English Live2D developer logs and explanatory comments.
- English-first server prompt context, weekday names, error messages, and the standalone EdgeTTS default voice.
- English descriptions and responses for device calling, changing assistant personality, exit intent, weather, news sources, and the lunar calendar.
- Compatibility aliases for original Chinese role names and RSS category names.
- The original database migration history has **not** been edited.

## Chinese text intentionally preserved

Certain Chinese strings are **data or protocol values**, not untranslated UI:

- `zh_CN.js`, `zh_TW.js`, `zh_CN.ts`, and locale-specific language bundles.
- Mandarin ASR examples, phonetic dictionaries, and wake-word phrases used by the bundled Chinese Sherpa/FunASR models.
- Chinese provider names used as exact `CHANNEL_MAP` keys for NewsNow (changing these would break source lookup).
- Legacy Chinese role/category aliases needed by existing devices and users.
- Audio reference transcripts that must match a recorded Mandarin sample.
- Chinese words used to recognize Mandarin device-binding and voice commands.
- Third-party model assets, identifiers, filenames, and historical Liquibase SQL migrations.

Do not remove these as part of a text-only localization.

## Remaining work before declaring full coverage

1. Audit remaining Python and Java source for user-visible messages or tool prompts still written in Chinese; separate these from comments and compatibility data.
2. Check seeded voice/model display labels currently stored in existing databases. If they need localization, use **new, forward-only Liquibase changesets** rather than editing applied migrations.
3. Review mobile and web console pages at runtime to catch untranslated responses from dynamic APIs and persisted user language settings.
4. Review any remaining technical notes, screenshots, and embedded text inside images.
5. Run and pass the repository's Python, Java, and Vue CI tests, and perform manual voice tests on an English-enabled device. Also smoke-test Chinese recognition to confirm compatibility.

## Validation

- `main/xiaozhi-server/mcp_server_settings.json` and `main/digital-human/js/config/default-mcp-tools.json` passed JSON parse checks.
- GitHub's **Tests** workflow has not yet completed for the current head of this long-running localization branch.
- A complete local app build and device/voice smoke test have not been performed in this environment.

**Status: In progress. Do not describe this branch as fully translated or merge-ready until the remaining audit and tests are complete.**
