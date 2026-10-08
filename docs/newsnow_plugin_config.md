# NewsNow News Source Configuration

## Overview

The `get_news_from_newsnow` plugin supports selecting news sources from the web management console, without changing program code. Each agent can use its own list.

## Configure news sources

### Option 1. Web management console (recommended)

1. Sign in to the management console.
2. Open **Agent Configuration** and select the agent.
3. Choose **Edit Functions** and find the **NewsNow News Aggregator** plugin.
4. In **News Sources**, enter the supported Chinese provider names separated by ASCII semicolons (`;`).
5. Save the function and agent configurations.

### Option 2. Configuration file

Edit your server configuration:

```yaml
plugins:
  get_news_from_newsnow:
    url: "https://newsnow.busiyi.world/api/s?id="
    news_sources: "澎湃新闻;百度热搜;财联社;微博;抖音"
```

## Source name format

**Important:** NewsNow uses Chinese source names as matching identifiers. These values **must remain in Chinese** and must match the plugin's `CHANNEL_MAP` entries exactly. Translating the labels in configuration would prevent the source lookup from working.

Use semicolons to separate the source IDs:

```text
澎湃新闻;百度热搜;财联社;微博;抖音;知乎;36氪
```

### Supported sources

| Chinese source ID (use in configuration) | English description |
| --- | --- |
| 澎湃新闻 | The Paper |
| 百度热搜 | Baidu trending searches |
| 财联社 | CLS finance news |
| 微博 | Weibo |
| 抖音 | Douyin |
| 知乎 | Zhihu |
| 36氪 | 36Kr |
| 华尔街见闻 | Wallstreetcn |
| IT之家 | IT Home |
| 今日头条 | Toutiao |
| 虎扑 | Hupu |
| 哔哩哔哩 | Bilibili |
| 快手 | Kuaishou |
| 雪球 | Xueqiu |
| 格隆汇 | Gelonghui |
| 法布财经 | Financial news source |
| 金十数据 | Jin10 |
| 牛客 | Nowcoder |
| 少数派 | Sspai |
| 稀土掘金 | Juejin |
| 凤凰网 | Phoenix News |
| 虫部落 | Chongbuluo |
| 联合早报 | Lianhe Zaobao |
| 酷安 | Coolapk |
| 远景论坛 | Yuanjing Forum |
| 参考消息 | Reference News |
| 卫星通讯社 | Sputnik |
| 百度贴吧 | Baidu Tieba |
| 靠谱新闻 | Kaopu News |

The plugin may expose additional sources as provider support evolves.

### Default sources

When no sources are configured, the plugin uses:

```text
澎湃新闻;百度热搜;财联社
```

## Usage

Ask Momo Companion to read the news, choose a configured source, or explain a particular story. Chinese voice requests are also supported, including `播报新闻` (read the news) and `详细介绍这条新闻` (explain this story).

## How it works

1. The plugin accepts the exact Chinese source label.
2. It maps the label to an API source ID, such as `thepaper`.
3. It requests articles from that provider and returns the content.

**Notes:** Names must match `CHANNEL_MAP`. Restart the server or reload its configuration after changes. Invalid selections fall back to defaults. Use ASCII `;`, not Chinese `；`, as the separator.
