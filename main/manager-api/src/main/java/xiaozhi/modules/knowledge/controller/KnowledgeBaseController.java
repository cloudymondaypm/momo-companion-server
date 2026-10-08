package xiaozhi.modules.knowledge.controller;

import java.util.*;

import org.apache.commons.lang3.StringUtils;
import org.apache.shiro.authz.annotation.RequiresPermissions;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import cn.hutool.core.collection.CollUtil;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.AllArgsConstructor;
import xiaozhi.common.exception.ErrorCode;
import xiaozhi.common.exception.RenException;
import xiaozhi.common.page.PageData;
import xiaozhi.common.utils.Result;
import xiaozhi.modules.knowledge.dto.KnowledgeBaseDTO;
import xiaozhi.modules.knowledge.service.KnowledgeBaseService;
import xiaozhi.modules.knowledge.service.KnowledgeManagerService;
import xiaozhi.modules.model.entity.ModelConfigEntity;
import xiaozhi.modules.security.user.SecurityUser;

@AllArgsConstructor
@RestController
@RequestMapping("/datasets")
@Tag(name = "Knowledge Base Management")
public class KnowledgeBaseController {

    private final KnowledgeBaseService knowledgeBaseService;
    private final KnowledgeManagerService knowledgeManagerService;

    @GetMapping
    @Operation(summary = "Get paginated knowledge base list")
    @RequiresPermissions("sys:role:normal")
    public Result<PageData<KnowledgeBaseDTO>> getPageList(
            @RequestParam(required = false) String name,
            @RequestParam(required = false, defaultValue = "1") Integer page,
            @RequestParam(required = false, defaultValue = "10") Integer page_size) {
        // Get current authenticated user ID
        Long currentUserId = SecurityUser.getUserId();

        KnowledgeBaseDTO knowledgeBaseDTO = new KnowledgeBaseDTO();
        knowledgeBaseDTO.setName(name);
        knowledgeBaseDTO.setCreator(currentUserId); // Set creator ID for access filtering

        PageData<KnowledgeBaseDTO> pageData = knowledgeBaseService.getPageList(knowledgeBaseDTO, page, page_size);
        return new Result<PageData<KnowledgeBaseDTO>>().ok(pageData);
    }

    @GetMapping("/{dataset_id}")
    @Operation(summary = "Get knowledge base by ID")
    @RequiresPermissions("sys:role:normal")
    public Result<KnowledgeBaseDTO> getByDatasetId(@PathVariable("dataset_id") String datasetId) {
        // Get current authenticated user ID
        Long currentUserId = SecurityUser.getUserId();

        KnowledgeBaseDTO knowledgeBaseDTO = knowledgeBaseService.getByDatasetId(datasetId);

        // Users can only view their own knowledge bases
        if (knowledgeBaseDTO.getCreator() == null || !knowledgeBaseDTO.getCreator().equals(currentUserId)) {
            throw new RenException(ErrorCode.NO_PERMISSION);
        }

        return new Result<KnowledgeBaseDTO>().ok(knowledgeBaseDTO);
    }

    @PostMapping
    @Operation(summary = "Create knowledge base")
    @RequiresPermissions("sys:role:normal")
    public Result<KnowledgeBaseDTO> save(@RequestBody @Validated KnowledgeBaseDTO knowledgeBaseDTO) {
        KnowledgeBaseDTO resp = knowledgeBaseService.save(knowledgeBaseDTO);
        return new Result<KnowledgeBaseDTO>().ok(resp);
    }

    @PutMapping("/{dataset_id}")
    @Operation(summary = "Update knowledge base")
    @RequiresPermissions("sys:role:normal")
    public Result<KnowledgeBaseDTO> update(@PathVariable("dataset_id") String datasetId,
            @RequestBody @Validated KnowledgeBaseDTO knowledgeBaseDTO) {
        // Get current authenticated user ID
        Long currentUserId = SecurityUser.getUserId();

        // Get existing knowledge base for permission check
        KnowledgeBaseDTO existingKnowledgeBase = knowledgeBaseService.getByDatasetId(datasetId);

        // Users can only update their own knowledge bases
        if (existingKnowledgeBase.getCreator() == null || !existingKnowledgeBase.getCreator().equals(currentUserId)) {
            throw new RenException(ErrorCode.NO_PERMISSION);
        }

        // [FIX] Inject ID to ensure Service finds the record
        knowledgeBaseDTO.setId(existingKnowledgeBase.getId());
        knowledgeBaseDTO.setDatasetId(datasetId);
        KnowledgeBaseDTO resp = knowledgeBaseService.update(knowledgeBaseDTO);
        return new Result<KnowledgeBaseDTO>().ok(resp);
    }

    @DeleteMapping("/{dataset_id}")
    @Operation(summary = "Delete one knowledge base")
    @Parameter(name = "dataset_id", description = "Knowledge base ID", required = true)
    @RequiresPermissions("sys:role:normal")
    public Result<Void> delete(@PathVariable("dataset_id") String datasetId) {
        // Get current authenticated user ID
        Long currentUserId = SecurityUser.getUserId();

        // Get existing knowledge base for permission check
        KnowledgeBaseDTO existingKnowledgeBase = knowledgeBaseService.getByDatasetId(datasetId);

        // Users can only delete their own knowledge bases
        if (existingKnowledgeBase.getCreator() == null || !existingKnowledgeBase.getCreator().equals(currentUserId)) {
            throw new RenException(ErrorCode.NO_PERMISSION);
        }

        // [Architecture Fix] Cascade deletes through orchestration to avoid orphan records and cyclic dependencies
        knowledgeManagerService.deleteDatasetWithFiles(datasetId);
        return new Result<>();
    }

    @DeleteMapping("/batch")
    @Operation(summary = "Bulk delete knowledge bases")
    @Parameter(name = "ids", description = "Knowledge base IDs, comma-separated", required = true)
    @RequiresPermissions("sys:role:normal")
    public Result<Void> deleteBatch(@RequestParam("ids") String ids) {
        if (StringUtils.isBlank(ids)) {
            throw new RenException(ErrorCode.PARAMS_GET_ERROR);
        }

        // Get current authenticated user ID
        Long currentUserId = SecurityUser.getUserId();
        List<String> idList = Arrays.asList(ids.split(","));
        List<KnowledgeBaseDTO> knowledgeBaseDTOs = Optional.ofNullable(knowledgeBaseService.getByDatasetIdList(idList))
                .orElseGet(ArrayList::new);
        if (CollUtil.isNotEmpty(knowledgeBaseDTOs)) {
            knowledgeBaseDTOs.forEach(item -> {
                // Users can only delete their own knowledge bases
                if (item.getCreator() == null || !item.getCreator().equals(currentUserId)) {
                    throw new RenException(ErrorCode.NO_PERMISSION);
                }
                // [Architecture Fix] Cascade delete through orchestration
                knowledgeManagerService.deleteDatasetWithFiles(item.getDatasetId());
            });
        }
        return new Result<>();
    }

    @GetMapping("/rag-models")
    @Operation(summary = "Get RAG model list")
    @RequiresPermissions("sys:role:normal")
    public Result<List<ModelConfigEntity>> getRAGModels() {
        List<ModelConfigEntity> result = knowledgeBaseService.getRAGModels();
        return new Result<List<ModelConfigEntity>>().ok(result);
    }
}
