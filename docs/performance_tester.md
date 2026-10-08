# Performance Testing Guide: ASR, LLM, Non-Streaming/Streaming TTS and Vision Models

1. Create a `data` directory under `main/xiaozhi-server`.
2. Create `data/.config.yaml`.
3. Put your ASR, LLM, streaming TTS and VLLM configuration in `data/.config.yaml`. For example:

```yaml
LLM:
  ChatGLMLLM:
    # OpenAI-compatible LLM adapter
    type: openai
    # glm-4-flash may be available at no charge but still requires an API key
    # Get one from https://bigmodel.cn/usercenter/proj-mgmt/apikeys
    model_name: glm-4-flash
    url: https://open.bigmodel.cn/api/paas/v4/
    api_key: YOUR_CHATGLM_API_KEY

TTS:

VLLM:

ASR:
```

4. Run the performance tester from `main/xiaozhi-server`:

```bash
python performance_tester.py
```

Configure your actual credentials and provider modules before running this example.
