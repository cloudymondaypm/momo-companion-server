package xiaozhi.modules.correctword.dto;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import lombok.Data;

@Data
@Schema(description = "Create replacement-word file DTO")
public class CorrectWordFileCreateDTO {

    @NotBlank(message = "File name is required")
    @Schema(description = "File name")
    private String fileName;

    @NotEmpty(message = "Replacement words are required")
    @Schema(description = "Replacement words; each item has original|replacement format")
    private List<String> content;

    @Schema(description = "File size in bytes, maximum 1 MB")
    private Long fileSize;
}
