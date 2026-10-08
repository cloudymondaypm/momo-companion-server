package xiaozhi.modules.knowledge.dto.document;

import lombok.*;
import io.swagger.v3.oas.annotations.media.Schema;
import java.io.Serializable;
import java.util.List;
import java.util.Map;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonAlias;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

/**
 * Document Management DTO
 */
@Schema(description = "Document Management DTO")
@JsonIgnoreProperties(ignoreUnknown = true)
public class DocumentDTO {

    /**
     * Document upload request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Document upload request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UploadReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Knowledge base ID (必须指定归属)", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("dataset_id")
        @NotBlank(message = "Knowledge base ID is required")
        private String datasetId;

        @Schema(description = "Filename (如果指定，则覆盖原始Filename)")
        private String name;

        @Schema(description = "Chunk method")
        @JsonProperty("chunk_method")
        private DocumentDTO.InfoVO.ChunkMethod chunkMethod;

        @Schema(description = "解析参数配置")
        @JsonProperty("parser_config")
        private DocumentDTO.InfoVO.ParserConfig parserConfig;

        @Schema(description = "Virtual folder path (默认为 /)")
        @JsonProperty("parent_path")
        private String parentPath;

        @Schema(description = "Metadata fields")
        @JsonProperty("meta")
        private Map<String, Object> metaFields;

        @Schema(description = "File binary stream (支持 PDF, DOCX, TXT, MD 等多种格式)", requiredMode = Schema.RequiredMode.REQUIRED)
        @NotNull(message = "Upload file is required")
        private org.springframework.web.multipart.MultipartFile file;
    }

    /**
     * Update document request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "Update document request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class UpdateReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "New document name (必须包含文件后缀，且不能更改原始类型)")
        private String name;

        @Schema(description = "Enable/disable状态 (true: 启用, false: 禁用; 禁用后不参与检索)")
        private Boolean enabled;

        @Schema(description = "New parser method (修改此项会重置解析状态)")
        @JsonProperty("chunk_method")
        private InfoVO.ChunkMethod chunkMethod;

        @Schema(description = "New parser settings (应与 chunk_method 配套使用)")
        @JsonProperty("parser_config")
        private InfoVO.ParserConfig parserConfig;
    }

    /**
     * List documents request
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "List documents request")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class ListReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Page number (默认: 1)")
        private Integer page;

        @Schema(description = "Page size (默认: 30)")
        @JsonProperty("page_size")
        private Integer pageSize;

        @Schema(description = "Sort field (可选: create_time, name, size; 默认: create_time)")
        private String orderby;

        @Schema(description = "Descending order (true: 最新/最大在前; false: 最旧/最小在前; 默认: true)")
        private Boolean desc;

        @Schema(description = "Exact filter: Document ID")
        private String id;

        @Schema(description = "Exact filter: 文档完整名称 (含后缀)")
        private String name;

        @Schema(description = "Fuzzy search: Document name关键词")
        private String keywords;

        @Schema(description = "Filter: 文件后缀列表 (如 ['pdf', 'docx'])")
        private List<String> suffix;

        @Schema(description = "Filter: 运行状态列表")
        private List<InfoVO.RunStatus> run;

        @Schema(description = "Filter: 起始Created at (时间戳, 毫秒)")
        @JsonProperty("create_time_from")
        private Long createTimeFrom;

        @Schema(description = "Filter: 结束Created at (时间戳, 毫秒)")
        @JsonProperty("create_time_to")
        private Long createTimeTo;
    }

    /**
     * 批量文档操作请求参数 (用于删除、解析等)
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "批量文档操作请求参数")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class BatchIdReq implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Document ID 列表", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("ids") // 为了兼容性，也可以考虑支持 document_ids，但这里统一叫 ids
        @JsonAlias("document_ids")
        @NotEmpty(message = "文档ID列表不能为空")
        private List<String> ids;
    }

    /**
     * 知识库文档信息 VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    @Schema(description = "知识库文档信息")
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class InfoVO implements Serializable {
        private static final long serialVersionUID = 1L;

        @Schema(description = "Document ID (唯一标识)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String id;

        @Schema(description = "Document thumbnail URL (Base64 或 链接)")
        private String thumbnail;

        @Schema(description = "Parent knowledge base ID", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("dataset_id")
        private String datasetId;

        @Schema(description = "Document parsing method (决定了文档如何被切片)")
        @JsonProperty("chunk_method")
        private ChunkMethod chunkMethod;

        @Schema(description = "关联的 ETL Pipeline ID (如有)")
        @JsonProperty("pipeline_id")
        private String pipelineId;

        @Schema(description = "Detailed document parser settings")
        @JsonProperty("parser_config")
        private ParserConfig parserConfig;

        @Schema(description = "来源类型 (如 local, s3, url 等)")
        @JsonProperty("source_type")
        private String sourceType;

        @Schema(description = "Document file type (如 pdf, docx, txt)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String type;

        @Schema(description = "Creator user ID")
        @JsonProperty("created_by")
        private String createdBy;

        @Schema(description = "Document name (包含扩展名)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String name;

        @Schema(description = "File storage path or identifier")
        private String location;

        @Schema(description = "File size (单位: Bytes)")
        private Long size;

        @Schema(description = "Total tokens contained (解析后统计)")
        @JsonProperty("token_count")
        private Long tokenCount;

        @Schema(description = "Contained chunks (Chunk) 总数")
        @JsonProperty("chunk_count")
        private Long chunkCount;

        @Schema(description = "Parsing progress (0.0 ~ 1.0, 1.0 表示完成)")
        private Double progress;

        @Schema(description = "Current progress description or error")
        @JsonProperty("progress_msg")
        private String progressMsg;

        @Schema(description = "Processing start time (RAGFlow返回RFC1123格式)")
        @JsonProperty("process_begin_at")
        private String processBeginAt;

        @Schema(description = "Total processing time (单位: 秒)")
        @JsonProperty("process_duration")
        private Double processDuration;

        @Schema(description = "Custom metadata fields (Key-Value 键值对)")
        @JsonProperty("meta_fields")
        private Map<String, Object> metaFields;

        @Schema(description = "File extension (不含点)")
        private String suffix;

        @Schema(description = "Document parsing run status")
        private RunStatus run;

        @Schema(description = "Document availability (1: 启用/正常, 0: 禁用/失效)", requiredMode = Schema.RequiredMode.REQUIRED)
        private String status;

        @Schema(description = "Created at (时间戳, 毫秒)", requiredMode = Schema.RequiredMode.REQUIRED)
        @JsonProperty("create_time")
        private Long createTime;

        @Schema(description = "Creation date (RAGFlow返回RFC1123格式)")
        @JsonProperty("create_date")
        private String createDate;

        @Schema(description = "Last updated at (时间戳, 毫秒)")
        @JsonProperty("update_time")
        private Long updateTime;

        @Schema(description = "Last updated (RAGFlow返回RFC1123格式)")
        @JsonProperty("update_date")
        private String updateDate;

        /**
         * Parsing method enum (ChunkMethod)
         */
        public enum ChunkMethod {
            @Schema(description = "通用模式: 适用于大多数纯文本或混合文档")
            @JsonProperty("naive")
            NAIVE,
            @Schema(description = "手动模式: 允许用户手动编辑切片")
            @JsonProperty("manual")
            MANUAL,
            @Schema(description = "问答模式: 专门优化 Q&A 格式的文档")
            @JsonProperty("qa")
            QA,
            @Schema(description = "表格模式: 专门优化 Excel 或 CSV 等表格数据")
            @JsonProperty("table")
            TABLE,
            @Schema(description = "论文模式: 针对学术论文排版优化")
            @JsonProperty("paper")
            PAPER,
            @Schema(description = "书籍模式: 针对书籍章节结构优化")
            @JsonProperty("book")
            BOOK,
            @Schema(description = "法律法规模式: 针对法律条文结构优化")
            @JsonProperty("laws")
            LAWS,
            @Schema(description = "演示文稿模式: 针对 PPT 等演示文件优化")
            @JsonProperty("presentation")
            PRESENTATION,
            @Schema(description = "图片模式: 针对图片内容进行 OCR 和描述")
            @JsonProperty("picture")
            PICTURE,
            @Schema(description = "整体模式: 将整个文档作为一个切片")
            @JsonProperty("one")
            ONE,
            @Schema(description = "知识Graph模式: 提取实体关系构建Graph")
            @JsonProperty("knowledge_graph")
            KNOWLEDGE_GRAPH,
            @Schema(description = "邮件模式: 针对邮件格式优化")
            @JsonProperty("email")
            EMAIL;
        }

        /**
         * Run status enum (RunStatus)
         */
        public enum RunStatus {
            @Schema(description = "未开始: 等待解析队列")
            @JsonProperty("UNSTART")
            UNSTART,
            @Schema(description = "进行中: 正在解析或索引")
            @JsonProperty("RUNNING")
            RUNNING,
            @Schema(description = "已取消: 用户手动取消")
            @JsonProperty("CANCEL")
            CANCEL,
            @Schema(description = "已完成: 解析成功")
            @JsonProperty("DONE")
            DONE,
            @Schema(description = "失败: 解析过程中出错")
            @JsonProperty("FAIL")
            FAIL;
        }

        /**
         * Layout detection enum
         */
        public enum LayoutRecognize {
            @Schema(description = "深度文档理解模型: 适合复杂排版")
            @JsonProperty("DeepDOC")
            DeepDOC,
            @Schema(description = "简单规则模型: 适合纯文本")
            @JsonProperty("Simple")
            Simple;
        }

        @Data
        @Builder
        @NoArgsConstructor
        @AllArgsConstructor
        @Schema(description = "文档解析器参数配置")
        @JsonIgnoreProperties(ignoreUnknown = true)
        public static class ParserConfig implements Serializable {
            private static final long serialVersionUID = 1L;

            @Schema(description = "Max tokens per chunk (建议值: 512, 1024, 2048)")
            @JsonProperty("chunk_token_num")
            private Integer chunkTokenNum;

            @Schema(description = "Section delimiter (支持转义字符, 如 \\n)")
            private String delimiter;

            @Schema(description = "Layout detection model (DeepDOC/Simple)")
            @JsonProperty("layout_recognize")
            private LayoutRecognize layoutRecognize;

            @Schema(description = "是否将 Excel 转换为 HTML 表格")
            @JsonProperty("html4excel")
            private Boolean html4excel;

            @Schema(description = "Extracted keyword count (0 表示不提取)")
            @JsonProperty("auto_keywords")
            private Integer autoKeywords;

            @Schema(description = "Auto-generated question count (0 表示不生成)")
            @JsonProperty("auto_questions")
            private Integer autoQuestions;

            @Schema(description = "Auto-generated tags")
            @JsonProperty("topn_tags")
            private Integer topnTags;

            @Schema(description = "RAPTOR 高级索引配置")
            private RaptorConfig raptor;

            @Schema(description = "GraphRAG 知识Graph配置")
            @JsonProperty("graphrag")
            private GraphRagConfig graphRag;

            @Data
            @Builder
            @NoArgsConstructor
            @AllArgsConstructor
            @Schema(description = "RAPTOR (递归摘要索引) 配置")
            @JsonIgnoreProperties(ignoreUnknown = true)
            public static class RaptorConfig implements Serializable {
                private static final long serialVersionUID = 1L;
                @Schema(description = "Whether enabled RAPTOR 索引")
                @JsonProperty("use_raptor")
                private Boolean useRaptor;
            }

            @Data
            @Builder
            @NoArgsConstructor
            @AllArgsConstructor
            @Schema(description = "GraphRAG (图增强检索) 配置")
            @JsonIgnoreProperties(ignoreUnknown = true)
            public static class GraphRagConfig implements Serializable {
                private static final long serialVersionUID = 1L;
                @Schema(description = "Whether enabled GraphRAG 索引")
                @JsonProperty("use_graphrag")
                private Boolean useGraphRag;
            }
        }
    }
}
