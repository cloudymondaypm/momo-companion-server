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

        @Schema(description = "Update keyword list (overwrites existing list)")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Enable/disable (true: enabled, false: disabled)")
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

        @Schema(description = "Page number (default 1)")
        private Integer page;

        @Schema(description = "Page size (default 30)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Search keywords (full-text search)")
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

        @Schema(description = "Chunk ID (typically document_id + index)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String id;

        @Schema(description = "Chunk text (primary target for full-text search)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String content;

        @Schema(description = "Parent document ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("document_id")
        private String documentId;

        @Schema(description = "Document name / keywords")
        @JsonProperty("docnm_kwd")
        private String docnmKwd;

        @Schema(description = "Important keywords (for enhanced keyword retrieval)")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Suggested questions (for Q&A enhancement)")
        private List<String> questions;

        @Schema(description = "Related image ID")
        @JsonProperty("image_id")
        private String imageId;

        @Schema(description = "Parent knowledge base ID")
        @JsonProperty("dataset_id")
        private String datasetId;

        @Schema(description = "Whether chunk is available (true: included in retrieval, false: excluded from retrieval)")
        private Boolean available;

        @Schema(description = "Location indices in source document (RAGFlow returns nested arrays, e.g. [[start, end, filename]])")
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
