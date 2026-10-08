package xiaozhi.modules.agent.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Agent memory update DTO
 */
@Data
@Schema(description = "Agent memory update payload")
public class AgentMemoryDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Memory summary", example = "Maintain a compact, evolving memory of important information over time.\n" +
            "Summarize important user information from conversations to personalize future assistance.", requiredMode = Schema.RequiredMode.NOT_REQUIRED)
    private String summaryMemory;
}
