# PowerMem Memory Integration Guide

## Overview

[PowerMem](https://www.powermem.ai/) is an open-source agent memory project from OceanBase. It uses language models to summarize conversations, stores extracted information, and supports semantic retrieval.

PowerMem itself is open source. Operating costs depend on the LLM, embeddings, and database you choose. A local/SQLite configuration with free-tier models can have minimal cost, whereas paid API and cloud database usage may incur charges. Check your provider's current limits.

- [GitHub repository](https://github.com/oceanbase/powermem)
- [Official website](https://www.powermem.ai/)
- [Usage examples](https://github.com/oceanbase/powermem/tree/main/examples)

## Features

- **Summarization:** Extract and retain useful information from conversations.
- **User profiles:** With `UserMemory`, automatically infer and update non-sensitive user information such as interests and preferences.
- **Adaptive forgetting:** Reduce the influence of stale or noisy memories.
- **Storage:** OceanBase, SeekDB, PostgreSQL, or SQLite, depending on the chosen features.
- **Language models:** Compatible Qwen, Zhipu, OpenAI, and other supported providers.
- **Semantic search:** Retrieve memories by embedding similarity.
- **Private deployment:** Keep the memory database on your own infrastructure.
- **Asynchronous operation:** Store and retrieve without unnecessarily blocking conversations.

## Installation

PowerMem is included in the project's dependencies. If you need to install it manually:

```bash
pip install powermem
```

## Basic configuration

Add PowerMem to your server configuration (`data/.config.yaml` for standalone deployments):

```yaml
selected_module:
  Memory: powermem

Memory:
  powermem:
    type: powermem
    # User profiles supported by selected storage backends
    enable_user_profile: true

    llm:
      provider: openai  # Alternatives include qwen, openai, zhipu
      config:
        api_key: YOUR_LLM_API_KEY
        model: qwen-plus

    embedder:
      provider: openai
      config:
        api_key: YOUR_EMBEDDING_API_KEY
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
        # embedding_dims: 1024

    vector_store:
      provider: sqlite
      config: {}  # No additional SQLite configuration
```

Keep the provider/model combination consistent. For example, a Qwen-compatible LLM using the OpenAI adapter may require a DashScope-compatible base URL.

### Configuration parameters

| Key | Description | Example options |
| --- | --- | --- |
| `llm.provider` | LLM provider adapter | `qwen`, `openai`, `zhipu` |
| `llm.config.api_key` | LLM API key | Provider-specific |
| `llm.config.model` | LLM model name | Provider-specific |
| `llm.config.openai_base_url` | Override LLM API base URL | Optional |
| `embedder.provider` | Embedding provider | `qwen`, `openai` |
| `embedder.config.api_key` | Embedding API key | Provider-specific |
| `embedder.config.model` | Embedding model name | Provider-specific |
| `embedder.config.openai_base_url` | Embedding API base URL | Optional |
| `vector_store.provider` | Memory storage backend | `oceanbase`, `seekdb`, `postgres`, `sqlite` |
| `vector_store.config` | Database connection settings | Depends on backend |

## Memory modes

| Mode | Setting | Behavior |
| --- | --- | --- |
| Standard memory | `enable_user_profile: false` | Conversation memory storage and search |
| User profiling | `enable_user_profile: true` | Memory plus automatic extraction of user preferences/profile information |

According to the upstream guide, PowerMem version 0.3.0+ supports `UserMemory` with OceanBase, SeekDB, or SQLite. Other storage backends may not support all profiling features.

## Provider examples

### Qwen (Alibaba Cloud Bailian)

Register through the [Bailian console](https://bailian.console.aliyun.com/) and obtain a key from [API Key Management](https://bailian.console.aliyun.com/?apiKey=1#/api-key).

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: qwen
      config:
        api_key: YOUR_QWEN_KEY
        model: qwen-plus
    embedder:
      provider: openai
      config:
        api_key: YOUR_QWEN_KEY
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    vector_store:
      provider: sqlite
      config: {}
```

### Zhipu AI

Zhipu provides the `glm-4-flash` family and embedding models. Verify current free-tier limits at the [Zhipu console](https://bigmodel.cn/usercenter/proj-mgmt/apikeys).

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: openai
      config:
        api_key: YOUR_ZHIPU_API_KEY
        model: glm-4-flash
        openai_base_url: https://open.bigmodel.cn/api/paas/v4/
    embedder:
      provider: openai
      config:
        api_key: YOUR_ZHIPU_API_KEY
        model: embedding-3
        openai_base_url: https://open.bigmodel.cn/api/paas/v4/
    vector_store:
      provider: sqlite
      config: {}
```

### OpenAI

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: openai
      config:
        api_key: YOUR_OPENAI_API_KEY
        model: gpt-4o-mini
        openai_base_url: https://api.openai.com/v1
    embedder:
      provider: openai
      config:
        api_key: YOUR_OPENAI_API_KEY
        model: text-embedding-3-small
        openai_base_url: https://api.openai.com/v1
    vector_store:
      provider: sqlite
      config: {}
```

### OceanBase

Deploy [OceanBase](https://github.com/oceanbase/oceanbase) locally or use its [cloud services](https://www.oceanbase.com/). Replace the SQLite block with:

```yaml
vector_store:
  provider: oceanbase
  config:
    host: 127.0.0.1
    port: 2881
    user: root@test
    password: YOUR_DATABASE_PASSWORD
    db_name: powermem
    collection_name: memories
    embedding_model_dims: 1536
```

Set `embedding_model_dims` to match your actual embedding model (1536 is an example, not a universal default). Protect database credentials.

## Memory isolation by device

According to this integration, PowerMem uses `device_id` as the memory `user_id`:

- Each device has its own isolated memory space.
- Different devices do not automatically share a memory history.
- Repeated conversations on the same device can reuse its context.

If you need cross-device memory for one human user, design a stable user identity and review privacy/consent implications before changing this isolation model.

## User profiles (`UserMemory`)

Set `enable_user_profile: true` to let PowerMem extract useful profile information alongside conversation memories:

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    vector_store:
      provider: sqlite
      config: {}
```

This abbreviated snippet illustrates only the switch and database; keep your existing `llm` and `embedder` settings when updating the actual configuration.

The profile may accumulate preferences, interests, and other information, combine them with semantic retrieval, and de-emphasize outdated details. Ensure users understand what information is retained.

## Comparison with other memory modules

| Feature | PowerMem | mem0ai | mem_local_short |
| --- | --- | --- | --- |
| Implementation | LLM-backed summarization | Remote memory API | Local summarization |
| Storage | Local or cloud DB | Cloud | Local YAML |
| Cost | Depends on model and database | Depends on provider tier | Primarily local resources |
| Retrieval | Vector similarity | Vector similarity | Stored content |
| User profiling | UserMemory | Depends on provider/version | Not in the upstream implementation |
| Adaptive forgetting | Supported | Depends on provider/version | Not in the upstream implementation |
| Private deployment | Yes | Depends on service | Yes |

## Troubleshooting

**API key error:** Verify `llm.config.api_key` and `embedder.config.api_key` are present, valid, and authorized for the selected models.

**Model not found:** Verify provider-specific model names and whether your account has access.

**Connection timeouts:** Check network access and the correct `openai_base_url` for the chosen LLM/embedding API.

## Import tests

```bash
source .venv/bin/activate
python -c "from powermem import AsyncMemory; print('PowerMem import successful')"
python -c "from powermem import UserMemory; print('UserMemory import successful')"
```

## Additional resources

- [PowerMem documentation](https://www.powermem.ai/)
- [PowerMem GitHub](https://github.com/oceanbase/powermem)
- [PowerMem examples](https://github.com/oceanbase/powermem/tree/main/examples)
- [OceanBase](https://www.oceanbase.com/)
- [SeekDB](https://github.com/oceanbase/seekdb)
- [Alibaba Cloud Bailian](https://bailian.console.aliyun.com/)
