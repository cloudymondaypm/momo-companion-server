package xiaozhi.modules.model.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "Voice details")
public class VoiceDTO implements Serializable {
    private static final long serialVersionUID = 1L;

    @Schema(description = "Voice ID")
    private String id;

    @Schema(description = "Voice name")
    private String name;

    @Schema(description = "Audio playback URL")
    private String voiceDemo;
    
    @Schema(description = "Language type")
    private String languages;
    
    @Schema(description = "Is cloned voice")
    private Boolean isClone;

    // Add two-parameter constructor for compatibility
    public VoiceDTO(String id, String name) {
        this.id = id;
        this.name = name;
        this.voiceDemo = null;
        this.languages = null;
        this.isClone = false; // Not a cloned voice by default
    }
    
    // Add three-parameter constructor for regular voice
    public VoiceDTO(String id, String name, String voiceDemo) {
        this.id = id;
        this.name = name;
        this.voiceDemo = voiceDemo;
        this.languages = null;
        this.isClone = false;
    }

}