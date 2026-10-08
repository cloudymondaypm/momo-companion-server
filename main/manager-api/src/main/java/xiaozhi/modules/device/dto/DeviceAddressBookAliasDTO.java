package xiaozhi.modules.device.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "Update device address book alias")
public class DeviceAddressBookAliasDTO {

    @NotBlank(message = "MAC address is required")
    @Schema(description = "This device's MAC address")
    private String macAddress;

    @NotBlank(message = "Target MAC address is required")
    @Schema(description = "Other device's MAC address")
    private String targetMac;

    @Schema(description = "Nickname for other device")
    private String alias;
}