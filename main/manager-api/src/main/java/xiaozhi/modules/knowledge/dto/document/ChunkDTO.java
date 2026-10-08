package xiaozhi.modules.knowledge.dto.document;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

/**
 * Chunk Management DTO
 */
@Schema(description = "Chunk Management DTO")
@JsonIgnoreProperties(ignoreUnknown = true)
public class ChunkDTO {

    /**
     * Create chunk request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Create chunk request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AddReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Chunk content", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotBlank(message = "Chunk content is required")
        private String content;

        @Schema(description = "Important keywords")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Suggested questions")
        private List<String> questions;
    }

    /**
     * Update chunk request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Update chunk request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UpdateReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "New chunk content")
        private String content;

        @Schema(description = "Update keyword list (覆盖原有列表)")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Enable/disable (true: 启用, false: 禁用)")
        private Boolean available;
    }

    /**
     * List chunks request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "List chunks request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ListReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Page number (默认 1)")
        private Integer page;

        @Schema(description = "Page size (默认 30)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Search keywords (全文检索)")
        private String keywords;

        @Schema(description = "Exact chunk ID")
        private String id;
    }

    /**
     * Bulk delete chunks request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Bulk delete chunks request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class RemoveReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Chunk IDs", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("chunk_ids")
        @NotEmpty(message = "Chunk IDs are required")
        private List<String> chunkIds;
    }

    /**
     * Document chunk information VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Document chunk information")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class InfoVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Chunk ID (通常为 document_id + 索引)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String id;

        @Schema(description = "Chunk text (全文检索的主要对象)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String content;

        @Schema(description = "Parent document ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("document_id")
        private String documentId;

        @Schema(description = "Document name / keywords")
        @JsonProperty("docnm_kwd")
        private String docnmKwd;

        @Schema(description = "Important keywords (用于关键词增强检索)")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Suggested questions (用于 Q&A 模式增强)")
        private List<String> questions;

        @Schema(description = "关联的Image ID")
        @JsonProperty("image_id")
        private String imageId;

        @Schema(description = "Parent knowledge base ID")
        @JsonProperty("dataset_id")
        private String datasetId;

        @Schema(description = "切片是否可用 (true: 参与检索, false: 被禁用)")
        private Boolean available;

        @Schema(description = "切片在原文中的Location indices列表 (RAGFlow返回嵌套数组, 如 [[start, end, filename]])")
        private List<List<Object>> positions;

        @Schema(description = "Token IDs")
        @JsonProperty("token")
        private List<Integer> token;
    }

    /**
     * Chunk list response
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Chunk list response")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ListVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Chunk list")
        private List<InfoVO> chunks;

        @Schema(description = "Related document details")
        private DocumentDTO.InfoVO doc;

        @Schema(description = "Total records")
        private Long total;
    }
}
