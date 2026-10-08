package xiaozhi.modules.device.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Getter;
import lombok.Setter;

import java.io.Serializable;
import java.util.List;

@Setter
@Getter
@Schema(description = "Device firmware report payload")
public class DeviceReportReqDTO implements Serializable {
    private static final long serialVersionUID = 1L;
    // region Entity fields
    @Schema(description = "Board firmware version")
    private Integer version;

    @Schema(description = "Flash size in bytes")
    @JsonProperty("flash_size")
    private Integer flashSize;

    @Schema(description = "Minimum free heap in bytes")
    @JsonProperty("minimum_free_heap_size")
    private Integer minimumFreeHeapSize;

    @Schema(description = "Device MAC address")
    @JsonProperty("mac_address")
    private String macAddress;

    @Schema(description = "Device unique identifier UUID")
    private String uuid;

    @Schema(description = "Chip model name")
    @JsonProperty("chip_model_name")
    private String chipModelName;

    @Schema(description = "Chip details")
    @JsonProperty("chip_info")
    private ChipInfo chipInfo;

    @Schema(description = "Application information")
    private Application application;

    @Schema(description = "Partition table list")
    @JsonProperty("partition_table")
    private List<Partition> partitionTable;

    @Schema(description = "Current running OTA partition")
    private OtaInfo ota;

    @Schema(description = "Board configuration")
    private BoardInfo board;

    // endregion

    @Getter
    @Setter
    @Schema(description = "Chip information")
    public static class ChipInfo {
        @Schema(description = "Chip model code")
        private Integer model;

        @Schema(description = "Number of cores")
        private Integer cores;

        @Schema(description = "Hardware revision")
        private Integer revision;

        @Schema(description = "Chip feature flags")
        private Integer features;
    }

    @Getter
    @Setter
    @Schema(description = "Board build information")
    public static class Application {
        @Schema(description = "Name")
        private String name;

        @Schema(description = "Application version")
        private String version;

        @Schema(description = "Build time (UTC ISO format)")
        @JsonProperty("compile_time")
        private String compileTime;

        @Schema(description = "ESP-IDF version")
        @JsonProperty("idf_version")
        private String idfVersion;

        @Schema(description = "ELF file SHA-256 checksum")
        @JsonProperty("elf_sha256")
        private String elfSha256;
    }

    @Getter
    @Setter
    @Schema(description = "Partition information")
    public static class Partition {
        @Schema(description = "Partition label")
        private String label;

        @Schema(description = "Partition type")
        private Integer type;

        @Schema(description = "Subtype")
        private Integer subtype;

        @Schema(description = "Start address")
        private Integer address;

        @Schema(description = "Partition size")
        private Integer size;
    }

    @Getter
    @Setter
    @Schema(description = "OTA信息")
    public static class OtaInfo {
        @Schema(description = "当前OTA标签")
        private String label;
    }

    @Getter
    @Setter
    @Schema(description = "板子连接和网络信息")
    public static class BoardInfo {
        @Schema(description = "板Subtype")
        private String type;

        @Schema(description = "连接的 Wi-Fi SSID")
        private String ssid;

        @Schema(description = "Wi-Fi 信号强度（RSSI）")
        private Integer rssi;

        @Schema(description = "Wi-Fi 信道")
        private Integer channel;

        @Schema(description = "IP 地址")
        private String ip;

        @Schema(description = "MAC 地址")
        private String mac;
    }
}
