import json
import httpx
from config.logger import setup_logging
from plugins_func.register import register_function, ToolType, ActionResponse, Action
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.connection import ConnectionHandler

TAG = __name__
logger = setup_logging()

# Define base function description template
SEARCH_FROM_RAGFLOW_FUNCTION_DESC = {
    "type": "function",
    "function": {
        "name": "search_from_ragflow",
        "description": "Search information in knowledge base",
        "parameters": {
            "type": "object",
            "properties": {"question": {"type": "string", "description": "Question to search for"}},
            "required": ["question"],
        },
    },
}


@register_function(
    "search_from_ragflow", SEARCH_FROM_RAGFLOW_FUNCTION_DESC, ToolType.SYSTEM_CTL
)
async def search_from_ragflow(conn: "ConnectionHandler", question=None):
    # Ensure string arguments are encoded correctly
    if question and isinstance(question, str):
        # Ensure question is UTF-8 text
        pass
    else:
        question = str(question) if question is not None else ""

    ragflow_config = conn.config.get("plugins", {}).get("search_from_ragflow", {})
    base_url = ragflow_config.get("base_url", "")
    api_key = ragflow_config.get("api_key", "")
    dataset_ids = ragflow_config.get("dataset_ids", [])

    url = base_url + "/api/v1/retrieval"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    # Ensure all payload strings use UTF-8
    payload = {"question": question, "dataset_ids": dataset_ids}

    try:
        # Use ensure_ascii=False so JSON correctly preserves non-ASCII text
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0), verify=False) as client:
            response = await client.post(url, json=payload, headers=headers)

        # Explicitly use UTF-8 response encoding
        response.encoding = "utf-8"

        response.raise_for_status()

        # Read text first and decode JSON manually
        response_text = response.text

        result = json.loads(response_text)

        if result.get("code") != 0:
            error_detail = result.get("error", {}).get("detail", "Unknown error")
            error_message = result.get("error", {}).get("message", "")
            error_code = result.get("code", "")

            # Safely log error details
            logger.bind(tag=TAG).error(
                f"RAGFlow API request failed, status:{error_code}; Error details:{error_detail}; Full response:{result}"
            )

            # Build detailed error response
            error_response = f"RAG API returned an error (code:{error_code}）"

            if error_message:
                error_response += f"：{error_message}"
            if error_detail:
                error_response += f"\nDetails:{error_detail}"

            return ActionResponse(Action.RESPONSE, None, error_response)

        chunks = result.get("data", {}).get("chunks", [])
        contents = []
        for chunk in chunks:
            content = chunk.get("content", "")
            if content:
                # Safely handle response content
                if isinstance(content, str):
                    contents.append(content)
                elif isinstance(content, bytes):
                    contents.append(content.decode("utf-8", errors="replace"))
                else:
                    contents.append(str(content))

        if contents:
            # Format knowledge-base content as references
            context_text = f"# Knowledge base results for: {question}\n"
            context_text += "```\n\n\n".join(contents[:5])
            context_text += "\n```"
        else:
            context_text = "No relevant information was found in the knowledge base."
        return ActionResponse(Action.REQLLM, context_text, None)

    except httpx.TimeoutException as e:
        error_response = "RAG API request timed out"
        error_response += "\nPossible cause: RAGFlow is slow or network latency is high"
        error_response += "\nSolution: Retry later or check RAGFlow service performance"
        return ActionResponse(Action.RESPONSE, None, error_response)

    except httpx.HTTPStatusError as e:
        if hasattr(e.response, "status_code"):
            status_code = e.response.status_code
            error_response = f"RAG API HTTP error (status:{status_code}）"
            try:
                error_detail = e.response.json().get("error", {}).get("message", "")
                if error_detail:
                    error_response += f"\nError details:{error_detail}"
            except:
                pass
        else:
            error_response = f"RAG API HTTP exception:{str(e)}"
        return ActionResponse(Action.RESPONSE, None, error_response)

    except httpx.HTTPError as e:
        error_response = "Unable to connect to RAG API"
        error_response += "\nPossible cause: Incorrect RAGFlow service URL or service is stopped"
        error_response += "\nSolution: Verify RAGFlow URL and service status"
        return ActionResponse(Action.RESPONSE, None, error_response)

    except Exception as e:
        # Other errors
        error_type = type(e).__name__
        logger.bind(tag=TAG).error(
            f"RAGFlow processing error, type:{error_type}; Details:{str(e)}"
        )

        # Provide detailed error message
        error_response = f"RAG API processing exception ({error_type}）：{str(e)}"
        return ActionResponse(Action.RESPONSE, None, error_response)
