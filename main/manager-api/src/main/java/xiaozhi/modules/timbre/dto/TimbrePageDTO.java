package xiaozhi.modules.timbre.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Paginated voice list DTO
 * 
 * @author zjy
 * @since 2025-3-21
 */
@Data
@Schema(description = "Voice pagination parameters")
public class TimbrePageDTO {

    @Schema(description = "Corresponding TTS model ID")
    @NotBlank(message = "{timbre.ttsModelId.require}")
    private String ttsModelId;

    @Schema(description = "Voice name")
    private String name;

    @Schema(description = "页数")
    private String page;

    @Schema(description = "显示列数")
    private String limit;
}
