package xiaozhi.modules.agent.dto;

import java.util.Date;
import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import xiaozhi.modules.agent.dto.AgentTagDTO;

/**
 * Agent data transfer object
 * Transfers agent data between service and controller.
 */
@Data
@Schema(description = "Agent object")
public class AgentDTO {
    @Schema(description = "Agent code", example = "AGT_1234567890")
    private String id;

    @Schema(description = "Agent name", example = "Customer Support Assistant")
    private String agentName;

    @Schema(description = "TTS model name", example = "tts_model_01")
    private String ttsModelName;

    @Schema(description = "Voice name", example = "voice_01")
    private String ttsVoiceName;

    @Schema(description = "LLM model name", example = "llm_model_01")
    private String llmModelName;

    @Schema(description = "Vision model name", example = "vllm_model_01")
    private String vllmModelName;

    @Schema(description = "Memory model ID", example = "mem_model_01")
    private String memModelId;

    @Schema(description = "Role/persona prompt", example = "You are a professional support assistant who answers questions and helps users.")
    private String systemPrompt;

    @Schema(description = "Memory summary", example = "Maintain a compact, evolving memory of important information over time.\n" +
            "Summarize important user information from conversations to personalize future assistance.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    private String summaryMemory;

    @Schema(description = "Last connected at", example = "2024-03-20 10:00:00")
    private Date lastConnectedAt;

    @Schema(description = "Device count", example = "10")
    private Integer deviceCount;

    @Schema(description = "Tag list")
    private List<AgentTagDTO> tags;
}
