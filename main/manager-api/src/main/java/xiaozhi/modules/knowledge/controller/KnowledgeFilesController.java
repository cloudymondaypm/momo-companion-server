package xiaozhi.modules.knowledge.controller;

import java.util.List;
import java.util.Map;

import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springdoc.core.annotations.ParameterObject;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.knowledge.dto.KnowledgeBaseDTO;
import xiaozhi.modules.knowledge.dto.KnowledgeFilesDTO;
import xiaozhi.modules.knowledge.dto.document.ChunkDTO;
import xiaozhi.modules.knowledge.dto.document.DocumentDTO;
import xiaozhi.modules.knowledge.dto.document.RetrievalDTO;
import xiaozhi.modules.knowledge.service.KnowledgeBaseService;
import xiaozhi.modules.knowledge.service.KnowledgeFilesService;
import xiaozhi.modules.security.user.SecurityUser;

@AllArgsConstructor
@RestController
@RequestMapping("/datasets/{dataset_id}")
@Tag(name = "Knowledge Base Document Management")
public class KnowledgeFilesController {

    private final KnowledgeFilesService knowledgeFilesService;
    private final KnowledgeBaseService knowledgeBaseService;

    /**
     * Verify current user can modify specified knowledge base
     * 
     * @param datasetId Knowledge base ID
     */
    private void validateKnowledgeBasePermission(String datasetId) {
        // Get current authenticated user ID
        Long currentUserId = SecurityUser.getUserId();

        // Get knowledge base details
        KnowledgeBaseDTO knowledgeBase = knowledgeBaseService.getByDatasetId(datasetId);

        // Users can only modify their own knowledge bases
        if (knowledgeBase.getCreator() == null || !knowledgeBase.getCreator().equals(currentUserId)) {
            throw new RenException(ErrorCode.NO_PERMISSION);
        }
    }

    @GetMapping("/documents")
    @Operation(summary = "Get paginated document list")
    @RequiresPermissions("sys:role:normal")
    public Result<PageData<KnowledgeFilesDTO>> getPageList(
            @PathVariable("dataset_id") String datasetId,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String status,
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @RequestParam(required = false, defaultValue = "10") Integer page_size) {
        // Verify knowledge base access
        validateKnowledgeBasePermission(datasetId);

        // Build parameters
        KnowledgeFilesDTO knowledgeFilesDTO = new KnowledgeFilesDTO();
        knowledgeFilesDTO.setDatasetId(datasetId);
        knowledgeFilesDTO.setName(name);
        knowledgeFilesDTO.setStatus(status);
        PageData<KnowledgeFilesDTO> pageData = knowledgeFilesService.getPageList(knowledgeFilesDTO, page, page_size);
        return new Result<PageData<KnowledgeFilesDTO>>().ok(pageData);
    }

    @GetMapping("/documents/status/{status}")
    @Operation(summary = "Get paginated documents by status")
    @RequiresPermissions("sys:role:normal")
    public Result<PageData<KnowledgeFilesDTO>> getPageListByStatus(
            @PathVariable("dataset_id") String datasetId,
            @PathVariable("status") String status,
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @RequestParam(required = false, defaultValue = "10") Integer page_size) {
        // Verify knowledge base access
        validateKnowledgeBasePermission(datasetId);
        // Build parameters
        KnowledgeFilesDTO knowledgeFilesDTO = new KnowledgeFilesDTO();
        knowledgeFilesDTO.setDatasetId(datasetId);
        knowledgeFilesDTO.setStatus(status);
        PageData<KnowledgeFilesDTO> pageData = knowledgeFilesService.getPageList(knowledgeFilesDTO, page, page_size);
        return new Result<PageData<KnowledgeFilesDTO>>().ok(pageData);
    }

    @PostMapping("/documents")
    @Operation(summary = "Upload document to knowledge base")
    @RequiresPermissions("sys:role:normal")
    public Result<KnowledgeFilesDTO> uploadDocument(
            @PathVariable("dataset_id") String datasetId,
            @RequestParam("file") MultipartFile file,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) String chunkMethod,
            @RequestParam(required = false) String metaFields,
            @RequestParam(required = false) String parserConfig) {

        // Verify knowledge base access
        validateKnowledgeBasePermission(datasetId);

        KnowledgeFilesDTO resp = knowledgeFilesService.uploadDocument(datasetId, file, name,
                metaFields != null ? parseJsonMap(metaFields) : null,
                chunkMethod,
                parserConfig != null ? parseJsonMap(parserConfig) : null);
        return new Result<KnowledgeFilesDTO>().ok(resp);
    }

    @DeleteMapping("/documents")
    @Operation(summary = "Bulk delete documents")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> delete(@PathVariable("dataset_id") String datasetId,
            @RequestBody DocumentDTO.BatchIdReq req) {
        // Verify knowledge base access
        validateKnowledgeBasePermission(datasetId);

        knowledgeFilesService.deleteDocuments(datasetId, req);
        return new Result<>();
    }

    @DeleteMapping("/documents/{document_id}")
    @Operation(summary = "Delete document")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> deleteSingle(@PathVariable("dataset_id") String datasetId,
            @PathVariable("document_id") String documentId) {
        // Verify knowledge base access
        validateKnowledgeBasePermission(datasetId);

        DocumentDTO.BatchIdReq req = new DocumentDTO.BatchIdReq();
        req.setIds(java.util.Collections.singletonList(documentId));
        knowledgeFilesService.deleteDocuments(datasetId, req);
        return new Result<>();
    }

    @PostMapping("/chunks")
    @Operation(summary = "Parse document into chunks")
    @RequiresPermissions("sys:role:normal")
    public Result<Void> parseDocuments(@PathVariable("dataset_id") String datasetId,
            @RequestBody Map<String, List<String>> requestBody) {
        // Verify knowledge base access
        validateKnowledgeBasePermission(datasetId);

        List<String> documentIds = requestBody.get("document_ids");
        if (documentIds == null || documentIds.isEmpty()) {
            return new Result<Void>().error("document_ids parameter is required");
        }

        boolean success = knowledgeFilesService.parseDocuments(datasetId, documentIds);
        if (success) {
            return new Result<Void>();
        } else {
            return new Result<Void>().error("Document parsing failed; the document may still be processing");
        }
    }

    @GetMapping("/documents/{document_id}/chunks")
    @Operation(summary = "List chunks of selected document")
    @RequiresPermissions("sys:role:normal")
    public Result<ChunkDTO.ListVO> listChunks(
            @PathVariable("dataset_id") String datasetId,
            @PathVariable("document_id") String documentId,
            @RequestParam(name = "page", required = false, defaultValue = "1") Integer page,
            @RequestParam(name = "page_size", required = false, defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String keywords,
            @RequestParam(required = false) String id) {

        // Check authorization, including ownership and existence
        validateKnowledgeBasePermission(datasetId);

        // Build request object
        ChunkDTO.ListReq req = ChunkDTO.ListReq.builder()
                .page(page)
                .pageSize(pageSize)
                .keywords(keywords)
                .id(id)
                .build();

        // Fetch typed chunk list from service
        ChunkDTO.ListVO result = knowledgeFilesService.listChunks(datasetId, documentId, req);
        return new Result<ChunkDTO.ListVO>().ok(result);
    }

    @PostMapping("/retrieval-test")
    @Operation(summary = "Retrieval test")
    @RequiresPermissions("sys:role:normal")
    public Result<RetrievalDTO.ResultVO> retrievalTest(
            @PathVariable("dataset_id") String datasetId,
            @RequestBody RetrievalDTO.TestReq req) {

        // Verify knowledge base access
        validateKnowledgeBasePermission(datasetId);

        // If no knowledge base ID is given, use datasetId from path
        if (req.getDatasetIds() == null || req.getDatasetIds().isEmpty()) {
            req.setDatasetIds(java.util.Arrays.asList(datasetId));
        }

        // [Reinforce] Validate pagination to prevent RAGFlow negative slicing errors
        if (req.getPage() == null || req.getPage() < 1) {
            req.setPage(1);
        }
        if (req.getPageSize() == null || req.getPageSize() < 1) {
            req.setPageSize(100);
        }

        // Run retrieval service and return typed response
        RetrievalDTO.ResultVO result = knowledgeFilesService.retrievalTest(req);
        return new Result<RetrievalDTO.ResultVO>().ok(result);
    }

    /**
     * Parse JSON string into Map
     */
    private Map<String, Object> parseJsonMap(String jsonString) {
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            return objectMapper.readValue(jsonString, new TypeReference<Map<String, Object>>() {
            });
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse JSON string: " + jsonString, e);
        }
    }
}