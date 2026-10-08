package xiaozhi.modules.device.dto;

import java.io.Serializable;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Device unbind request
 */
@Data
@Schema(description = "Device unbind request")
public class DeviceUnBindDTO implements Serializable {

    @Schema(description = "Device ID")
    @NotBlank(message = "Device ID is required")
    private String deviceId;

}