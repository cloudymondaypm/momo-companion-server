package xiaozhi.modules.voiceclone.dto;

import java.util.Date;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

/**
 * Voice cloning response DTO
 * Provides voice cloning information to the UI including model and user names.
 */
@Data
@Schema(description = "Voice cloning response DTO")
public class VoiceCloneResponseDTO {

    @Schema(description = "Unique identifier")
    private String id;

    @Schema(description = "Voice name")
    private String name;

    @Schema(description = "Model ID")
    private String modelId;

    @Schema(description = "Model name")
    private String modelName;

    @Schema(description = "Voice ID")
    private String voiceId;

    @Schema(description = "Language")
    private String languages;

    @Schema(description = "User ID (linked account)")
    private Long userId;

    @Schema(description = "User name")
    private String userName;

    @Schema(description = "Training status: 0=pending, 1=training, 2=success, 3=failed")
    private Integer trainStatus;

    @Schema(description = "Training failure reason")
    private String trainError;

    @Schema(description = "Created at")
    private Date createDate;

    @Schema(description = "Audio data available")
    private Boolean hasVoice;
}