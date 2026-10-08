package xiaozhi.modules.config.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "Agent replacement-word DTO")
public class CorrectWordsDTO {

    @NotBlank(message = "Device MAC address is required")
    @Schema(description = "Device MAC address")
    private String macAddress;
}
