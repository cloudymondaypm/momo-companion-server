package xiaozhi.modules.sys.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import xiaozhi.modules.sys.enums.ServerActionEnum;

/**
 * Send Python server action DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class EmitSeverActionDTO
{
    @Schema(description = "Target WebSocket URL")
    @NotEmpty(message = "Target WebSocket address is required")
    private String targetWs;

    @Schema(description = "Requested action")
    @NotNull(message = "Action is required")
    private ServerActionEnum action;
}
