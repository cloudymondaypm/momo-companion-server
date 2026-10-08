package xiaozhi.modules.agent.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Data;

/**
 * Voiceprint identification response
 */
@Data
public class IdentifyVoicePrintResponse {
    /**
     * Best matching voiceprint ID
     */
    @JsonProperty("speaker_id")
    private String speakerId;
    /**
     * Voiceprint match score
     */
    private Double score;
}
