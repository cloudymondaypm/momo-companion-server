package xiaozhi.modules.device.dto;

import java.util.Map;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class DeviceToolsCallReqDTO {

    @NotBlank(message = "Tool name is required")
    private String name;

    private Map<String, Object> arguments;
}