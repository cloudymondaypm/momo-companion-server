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
     * 文档聚合信息 (VO)
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "文档聚合信息")
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

        @Schema(description = "Document ID 列表 (可选，用于限定检索范围)")
        @JsonProperty("document_ids")
        private List<String> documentIds;

        @Schema(description = "Retrieval query", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotBlank(message = "Retrieval question is required")
        private String question;

        @Schema(description = "Page number (默认 1)")
        private Integer page;

        @Schema(description = "Page size (默认 10)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Similarity threshold (默认 0.2)")
        @JsonProperty("similarity_threshold")
        private Float similarityThreshold;

        @Schema(description = "Vector similarity weight (默认 0.3)")
        @JsonProperty("vector_similarity_weight")
        private Float vectorSimilarityWeight;

        @Schema(description = "Return top K chunks (默认 1024)")
        @JsonProperty("top_k")
        private Integer topK;

        @Schema(description = "Reranker model ID")
        @JsonProperty("rerank_id")
        private String rerankId;

        @Schema(description = "Highlight keywords")
        private Boolean highlight;

        @Schema(description = "Enable keyword retrieval")
        private Boolean keyword;

        @Schema(description = "Cross-language translations (可选)")
        @JsonProperty("cross_languages")
        private List<String> crossLanguages;

        @Schema(description = "Metadata filters (JSON 对象)")
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

        @Schema(description = "文档关键词")
        @JsonProperty("document_keyword")
        private String documentKeyword;

        @Schema(description = "综合相似度", requiredMode = Schema.RequiredMode.REQUIRED)
        private Float similarity;

        @Schema(description = "向量相似度")
        @JsonProperty("vector_similarity")
        private Float vectorSimilarity;

        @Schema(description = "关键词相似度")
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

        @Schema(description = "Location indices (RAGFlow返回嵌套数组, 如 [[start, end, filename]])")
        private Object positions;
    }

    /**
     * 知识库元数据摘要 (VO)
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "知识库元数据摘要信息")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MetaSummaryVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Total documents", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("total_doc_count")
        private Long totalDocCount;

        @Schema(description = "Token 总数", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("total_token_count")
        private Long totalTokenCount;

        @Schema(description = "File type distribution (key: 文件后缀, value: Count)")
        @JsonProperty("file_type_distribution")
        private Map<String, Long> fileTypeDistribution;

        @Schema(description = "Document status distribution (key: 状态码, value: Count)")
        @JsonProperty("status_distribution")
        private Map<String, Long> statusDistribution;

        @Schema(description = "自定义Metadata statistics (key: 字段名, value: Count/值)")
        @JsonProperty("custom_metadata")
        private Map<String, Object> customMetadata;
    }

    /**
     * 批量更新元数据请求参数
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "批量更新元数据请求参数")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class MetaBatchReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Filter器: 用于指定要更新的文档范围 (默认全部)")
        private Selector selector;

        @Schema(description = "新增或更新的元数据列表")
        private List<UpdateItem> updates;

        @Schema(description = "Metadata keys to delete")
        private List<DeleteItem> deletes;

        /**
         * 文档Filter器
         */
        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "Metadata update filter")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class Selector implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "指定Document ID 列表")
            @JsonProperty("document_ids")
            private List<String> documentIds;

            @Schema(description = "Metadata condition matching (key: 字段名, value: 匹配值)")
            @JsonProperty("metadata_condition")
            private Map<String, Object> metadataCondition;
        }

        /**
         * 更新项
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
         * 删除项
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
