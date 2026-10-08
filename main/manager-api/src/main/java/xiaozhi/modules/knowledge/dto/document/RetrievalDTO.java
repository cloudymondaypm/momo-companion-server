package xiaozhi.modules.knowledge.dto.document;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

/**
 * Retrieval and Metadata Management DTO
 */
@Schema(description = "Retrieval and Metadata Management DTO")
@JsonIgnoreProperties(ignoreUnknown = true)
public class RetrievalDTO {

    /**
     * Document aggregation details (VO)
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Document aggregation details")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class DocAggVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Document name")
        @JsonProperty("doc_name")
        private String docName;

        @Schema(description = "Document ID")
        @JsonProperty("doc_id")
        private String docId;

        @Schema(description = "Count")
        private Integer count;
    }

    /**
     * Retrieval test request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Retrieval test request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    @JsonInclude(JsonInclude.Include.NON_NULL)
    public static class TestReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Knowledge base IDs", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("dataset_ids")
        @NotEmpty(message = "Knowledge base ID list is required")
        private List<String> datasetIds;

        @Schema(description = "Document ID list (optional, restrict retrieval scope)")
        @JsonProperty("document_ids")
        private List<String> documentIds;

        @Schema(description = "Retrieval query", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotBlank(message = "Retrieval question is required")
        private String question;

        @Schema(description = "Page number (default 1)")
        private Integer page;

        @Schema(description = "Page size (default 10)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Similarity threshold (default 0.2)")
        @JsonProperty("similarity_threshold")
        private Float similarityThreshold;

        @Schema(description = "Vector similarity weight (default 0.3)")
        @JsonProperty("vector_similarity_weight")
        private Float vectorSimilarityWeight;

        @Schema(description = "Return top K chunks (default 1024)")
        @JsonProperty("top_k")
        private Integer topK;

        @Schema(description = "Reranker model ID")
        @JsonProperty("rerank_id")
        private String rerankId;

        @Schema(description = "Highlight keywords")
        private Boolean highlight;

        @Schema(description = "Enable keyword retrieval")
        private Boolean keyword;

        @Schema(description = "Cross-language translations (optional)")
        @JsonProperty("cross_languages")
        private List<String> crossLanguages;

        @Schema(description = "Metadata filters (JSON object)")
        @JsonProperty("metadata_condition")
        private Map<String, Object> metadataCondition;
    }

    /**
     * Retrieval hit (VO)
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Matching chunk details")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class HitVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Chunk ID", requiredMode = Schema.RequiredMode.REQUIRED)
        private String id;

        @Schema(description = "Chunk content", requiredMode = Schema.RequiredMode.REQUIRED)
        private String content;

        @Schema(description = "Parent document ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("document_id")
        private String documentId;

        @Schema(description = "Parent knowledge base ID")
        @JsonProperty("dataset_id")
        private String datasetId;

        @Schema(description = "Document name")
        @JsonProperty("document_name")
        private String documentName;

        @Schema(description = "Document keywords")
        @JsonProperty("document_keyword")
        private String documentKeyword;

        @Schema(description = "Overall similarity", requiredMode = Schema.RequiredMode.REQUIRED)
        private Float similarity;

        @Schema(description = "Vector similarity")
        @JsonProperty("vector_similarity")
        private Float vectorSimilarity;

        @Schema(description = "Keyword similarity")
        @JsonProperty("term_similarity")
        private Float termSimilarity;

        @Schema(description = "Index position")
        private Integer index;

        @Schema(description = "Highlighted content")
        private String highlight;

        @Schema(description = "Important keywords")
        @JsonProperty("important_keywords")
        private List<String> importantKeywords;

        @Schema(description = "Suggested questions")
        private List<String> questions;

        @Schema(description = "Image ID")
        @JsonProperty("image_id")
        private String imageId;

        @Schema(description = "Location indices (RAGFlow returns nested arrays, e.g. [[start, end, filename]])")
        private Object positions;
    }

    /**
     * Knowledge base metadata summary (VO)
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Knowledge base metadata summary")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MetaSummaryVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Total documents", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("total_doc_count")
        private Long totalDocCount;

        @Schema(description = "Total tokens", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("total_token_count")
        private Long totalTokenCount;

        @Schema(description = "File type distribution (key: file extension, value: Count)")
        @JsonProperty("file_type_distribution")
        private Map<String, Long> fileTypeDistribution;

        @Schema(description = "Document status distribution (key: status code, value: Count)")
        @JsonProperty("status_distribution")
        private Map<String, Long> statusDistribution;

        @Schema(description = "Custom metadata statistics (key: field name, value: Count/value)")
        @JsonProperty("custom_metadata")
        private Map<String, Object> customMetadata;
    }

    /**
     * Bulk update metadata request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Bulk update metadata request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MetaBatchReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Filter: specifies the document scope (all by default)")
        private Selector selector;

        @Schema(description = "Metadata to create or updatelist")
        private List<UpdateItem> updates;

        @Schema(description = "Metadata keys to delete")
        private List<DeleteItem> deletes;

        /**
         * Document filter
         */
        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Metadata update filter")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class Selector implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Selected document IDs list")
            @JsonProperty("document_ids")
            private List<String> documentIds;

            @Schema(description = "Metadata condition matching (key: field name, value: matching value)")
            @JsonProperty("metadata_condition")
            private Map<String, Object> metadataCondition;
        }

        /**
         * Update item
         */
        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Metadata update item")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class UpdateItem implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Metadata key", requiredMode = Schema.RequiredMode.REQUIRED)
            private String key;

            @Schema(description = "Metadata value", requiredMode = Schema.RequiredMode.REQUIRED)
            private Object value;
        }

        /**
         * Delete item
         */
        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Metadata delete item")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class DeleteItem implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Metadata key to delete", requiredMode = Schema.RequiredMode.REQUIRED)
            private String key;
        }
    }

    /**
     * Retrieval test results
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Retrieval test results")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ResultVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Matched chunks")
        private List<HitVO> chunks;

        @Schema(description = "Document distribution")
        @JsonProperty("doc_aggs")
        private List<DocAggVO> docAggs;

        @Schema(description = "Total matched records")
        private Long total;
    }
}
