package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "Update device address book permissions")
public class DeviceAddressBookPermissionDTO {

    @NotBlank(message = "MAC address is required")
    @Schema(description = "This device MAC address")
    private String macAddress;

    @NotBlank(message = "Target MAC address is required")
    @Schema(description = "Other device MAC address")
    private String targetMac;

    @Schema(description = "Whether calls are allowed")
    private Boolean hasPermission;
}