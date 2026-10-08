package xiaozhi.modules.model.dto;

import java.io.Serializable;
import java.util.Date;

import com.baomidou.mybatisplus.annotation.FieldFill;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import xiaozhi.common.validator.group.UpdateGroup;

@Data
@Schema(description = "Model provider")
public class ModelProviderDTO implements Serializable {
    @Schema(description = "Primary key")
    @NotBlank(message = "ID is required", groups = UpdateGroup.class)
    private String id;

    @Schema(description = "Model type (Memory/ASR/VAD/LLM/TTS)")
    @NotBlank(message = "modelType is required")
    private String modelType;

    @Schema(description = "Provider type")
    @NotBlank(message = "providerCode is required")
    private String providerCode;

    @Schema(description = "Provider name")
    @NotBlank(message = "Name is required")
    private String name;

    @Schema(description = "Provider fields (JSON)")
    @TableField(typeHandler = JacksonTypeHandler.class)
    @NotBlank(message = "JSON fields are required")
    private String fields;

    @Schema(description = "Sort order")
    @NotNull(message = "Sort order is required")
    private Integer sort;

    @Schema(description = "Updated by")
    @TableField(fill = FieldFill.UPDATE)
    private Long updater;

    @Schema(description = "Updated at")
    @TableField(fill = FieldFill.UPDATE)
    private Date updateDate;

    @Schema(description = "Created by")
    @TableField(fill = FieldFill.INSERT)
    private Long creator;

    @Schema(description = "Created at")
    @TableField(fill = FieldFill.INSERT)
    private Date createDate;
}
