package xiaozhi.modules.agent.dto;

import lombok.Data;

/**
 * Update agent voiceprint DTO
 *
 * @author zjy
 */
@Data
public class AgentVoicePrintUpdateDTO {
    /**
     * Agent voiceprint ID
     */
    private String id;
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
