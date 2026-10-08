package xiaozhi.modules.agent.dto;

import lombok.Data;

/**
 * Save agent voiceprint DTO
 *
 * @author zjy
 */
@Data
public class AgentVoicePrintSaveDTO {
    /**
     * Associated agent ID
     */
    private String agentId;
    /**
     * Audio file ID
     */
    private String audioId;
    /**
     * Speaker name for voiceprint
     */
    private String sourceName;
    /**
     * Description of speaker
     */
    private String introduce;
}
