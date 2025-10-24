import asyncio
import os
import traceback
from urllib.parse import quote, unquote

from fastapi import APIRouter, Body, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.responses import FileResponse as StarletteFileResponse

from src.storage.db.models import User
from server.utils.auth_middleware import get_admin_user
from server.services.tasker import TaskContext, tasker
from src import config, knowledge_base
from src.knowledge.indexing import SUPPORTED_FILE_EXTENSIONS, is_supported_file_extension, process_file_to_markdown
from src.knowledge.utils import calculate_content_hash
from src.models.embed import test_embedding_model_status, test_all_embedding_models_status
from src.utils import hashstr, logger

knowledge = APIRouter(prefix="/knowledge", tags=["knowledge"])

# =============================================================================
# === 数据库管理分组 ===
# =============================================================================


@knowledge.get("/databases")
async def get_databases(current_user: User = Depends(get_admin_user)):
    """获取所有知识库"""
    try:
        database = knowledge_base.get_databases()
        return database
    except Exception as e:
        logger.error(f"获取数据库列表失败 {e}, {traceback.format_exc()}")
        return {"message": f"获取数据库列表失败 {e}", "databases": []}


@knowledge.post("/databases")
async def create_database(
    database_name: str = Body(...),
    description: str = Body(...),
    embed_model_name: str = Body(...),
    kb_type: str = Body("lightrag"),
    additional_params: dict = Body({}),
    llm_info: dict = Body(None),
    current_user: User = Depends(get_admin_user),
):
    """创建知识库"""
    logger.debug(
        f"Create database {database_name} with kb_type {kb_type}, "
        f"additional_params {additional_params}, llm_info {llm_info}"
    )
    try:
        embed_info = config.embed_model_names[embed_model_name]
        database_info = await knowledge_base.create_database(
            database_name, description, kb_type=kb_type, embed_info=embed_info, llm_info=llm_info, **additional_params
        )

        # 需要重新加载所有智能体，因为工具刷新了
        from src.agents import agent_manager

        await agent_manager.reload_all()

        return database_info
    except Exception as e:
        logger.error(f"创建数据库失败 {e}, {traceback.format_exc()}")
        return {"message": f"创建数据库失败 {e}", "status": "failed"}


@knowledge.get("/databases/{db_id}")
async def get_database_info(db_id: str, current_user: User = Depends(get_admin_user)):
    """获取知识库详细信息"""
    database = knowledge_base.get_database_info(db_id)
    if database is None:
        raise HTTPException(status_code=404, detail="Database not found")
    return database


@knowledge.put("/databases/{db_id}")
async def update_database_info(
    db_id: str, name: str = Body(...), description: str = Body(...), current_user: User = Depends(get_admin_user)
):
    """更新知识库信息"""
    logger.debug(f"Update database {db_id} info: {name}, {description}")
    try:
        database = await knowledge_base.update_database(db_id, name, description)
        return {"message": "更新成功", "database": database}
    except Exception as e:
        logger.error(f"更新数据库失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"更新数据库失败: {e}")


@knowledge.delete("/databases/{db_id}")
async def delete_database(db_id: str, current_user: User = Depends(get_admin_user)):
    """删除知识库"""
    logger.debug(f"Delete database {db_id}")
    try:
        await knowledge_base.delete_database(db_id)

        # 需要重新加载所有智能体，因为工具刷新了
        from src.agents import agent_manager

        await agent_manager.reload_all()

        return {"message": "删除成功"}
    except Exception as e:
        logger.error(f"删除数据库失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"删除数据库失败: {e}")


@knowledge.get("/databases/{db_id}/export")
async def export_database(
    db_id: str,
    format: str = Query("csv", enum=["csv", "xlsx", "md", "txt"]),
    include_vectors: bool = Query(False, description="是否在导出中包含向量数据"),
    current_user: User = Depends(get_admin_user),
):
    """导出知识库数据"""
    logger.debug(f"Exporting database {db_id} with format {format}")
    try:
        file_path = await knowledge_base.export_data(db_id, format=format, include_vectors=include_vectors)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Exported file not found.")

        media_types = {
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "md": "text/markdown",
            "txt": "text/plain",
        }
        media_type = media_types.get(format, "application/octet-stream")

        return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type=media_type)
    except NotImplementedError as e:
        logger.warning(f"A disabled feature was accessed: {e}")
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logger.error(f"导出数据库失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导出数据库失败: {e}")


# =============================================================================
# === 文档管理分组 ===
# =============================================================================


@knowledge.post("/databases/{db_id}/documents")
async def add_documents(
    db_id: str, items: list[str] = Body(...), params: dict = Body(...), current_user: User = Depends(get_admin_user)
):
    """添加文档到知识库"""
    logger.debug(f"Add documents for db_id {db_id}: {items} {params=}")

    content_type = params.get("content_type", "file")

    # 安全检查：验证文件路径
    if content_type == "file":
        from src.knowledge.utils.kb_utils import validate_file_path

        for item in items:
            try:
                validate_file_path(item, db_id)
            except ValueError as e:
                raise HTTPException(status_code=403, detail=str(e))

    async def run_ingest(context: TaskContext):
        await context.set_message("任务初始化")
        await context.set_progress(5.0, "准备处理文档")

        total = len(items)
        processed_items = []

        try:
            # 逐个处理文档并更新进度
            for idx, item in enumerate(items, 1):
                await context.raise_if_cancelled()

                # 更新进度
                progress = 5.0 + (idx / total) * 90.0  # 5% ~ 95%
                await context.set_progress(progress, f"正在处理第 {idx}/{total} 个文档")

                # 处理单个文档
                result = await knowledge_base.add_content(db_id, [item], params=params)
                processed_items.extend(result)

        except asyncio.CancelledError:
            await context.set_progress(100.0, "任务已取消")
            raise

        item_type = "URL" if content_type == "url" else "文件"
        failed_count = len([_p for _p in processed_items if _p.get("status") == "failed"])
        summary = {
            "db_id": db_id,
            "item_type": item_type,
            "submitted": len(processed_items),
            "failed": failed_count,
        }
        message = f"{item_type}处理完成，失败 {failed_count} 个" if failed_count else f"{item_type}处理完成"
        await context.set_result(summary | {"items": processed_items})
        await context.set_progress(100.0, message)
        return summary | {"items": processed_items}

    try:
        task = await tasker.enqueue(
            name=f"知识库文档处理({db_id})",
            task_type="knowledge_ingest",
            payload={
                "db_id": db_id,
                "items": items,
                "params": params,
                "content_type": content_type,
            },
            coroutine=run_ingest,
        )
        return {
            "message": "任务已提交，请在任务中心查看进度",
            "status": "queued",
            "task_id": task.id,
        }
    except Exception as e:  # noqa: BLE001
        logger.error(f"Failed to enqueue {content_type}s: {e}, {traceback.format_exc()}")
        return {"message": f"Failed to enqueue task: {e}", "status": "failed"}


@knowledge.get("/databases/{db_id}/documents/{doc_id}")
async def get_document_info(db_id: str, doc_id: str, current_user: User = Depends(get_admin_user)):
    """获取文档详细信息（包含基本信息和内容信息）"""
    logger.debug(f"GET document {doc_id} info in {db_id}")

    try:
        info = await knowledge_base.get_file_info(db_id, doc_id)
        return info
    except Exception as e:
        logger.error(f"Failed to get file info, {e}, {db_id=}, {doc_id=}, {traceback.format_exc()}")
        return {"message": "Failed to get file info", "status": "failed"}


@knowledge.get("/databases/{db_id}/documents/{doc_id}/basic")
async def get_document_basic_info(db_id: str, doc_id: str, current_user: User = Depends(get_admin_user)):
    """获取文档基本信息（仅元数据）"""
    logger.debug(f"GET document {doc_id} basic info in {db_id}")

    try:
        info = await knowledge_base.get_file_basic_info(db_id, doc_id)
        return info
    except Exception as e:
        logger.error(f"Failed to get file basic info, {e}, {db_id=}, {doc_id=}, {traceback.format_exc()}")
        return {"message": "Failed to get file basic info", "status": "failed"}


@knowledge.get("/databases/{db_id}/documents/{doc_id}/content")
async def get_document_content(db_id: str, doc_id: str, current_user: User = Depends(get_admin_user)):
    """获取文档内容信息（chunks和lines）"""
    logger.debug(f"GET document {doc_id} content in {db_id}")

    try:
        info = await knowledge_base.get_file_content(db_id, doc_id)
        return info
    except Exception as e:
        logger.error(f"Failed to get file content, {e}, {db_id=}, {doc_id=}, {traceback.format_exc()}")
        return {"message": "Failed to get file content", "status": "failed"}


@knowledge.delete("/databases/{db_id}/documents/{doc_id}")
async def delete_document(db_id: str, doc_id: str, current_user: User = Depends(get_admin_user)):
    """删除文档"""
    logger.debug(f"DELETE document {doc_id} info in {db_id}")
    try:
        await knowledge_base.delete_file(db_id, doc_id)
        return {"message": "删除成功"}
    except Exception as e:
        logger.error(f"删除文档失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"删除文档失败: {e}")


@knowledge.get("/databases/{db_id}/documents/{doc_id}/download")
async def download_document(db_id: str, doc_id: str, request: Request, current_user: User = Depends(get_admin_user)):
    """下载原始文件"""
    logger.debug(f"Download document {doc_id} from {db_id}")
    try:
        file_info = await knowledge_base.get_file_basic_info(db_id, doc_id)
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")

        file_path = file_info.get("meta", {}).get("path")
        if not file_path:
            raise HTTPException(status_code=404, detail="File path not found in metadata")

        # 安全检查：验证文件路径
        from src.knowledge.utils.kb_utils import validate_file_path

        try:
            normalized_path = validate_file_path(file_path, db_id)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))

        if not os.path.exists(normalized_path):
            raise HTTPException(status_code=404, detail=f"File not found on disk: {file_info=}")

        # 获取文件扩展名和MIME类型，解码URL编码的文件名
        filename = file_info.get("meta", {}).get("filename", "file")
        logger.debug(f"Original filename from database: {filename}")

        # 解码URL编码的文件名（如果有的话）
        try:
            decoded_filename = unquote(filename, encoding="utf-8")
            logger.debug(f"Decoded filename: {decoded_filename}")
        except Exception as e:
            logger.debug(f"Failed to decode filename {filename}: {e}")
            decoded_filename = filename  # 如果解码失败，使用原文件名

        _, ext = os.path.splitext(decoded_filename)

        media_types = {
            ".pdf": "application/pdf",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".doc": "application/msword",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".json": "application/json",
            ".csv": "text/csv",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".ppt": "application/vnd.ms-powerpoint",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".svg": "image/svg+xml",
            ".zip": "application/zip",
            ".rar": "application/x-rar-compressed",
            ".7z": "application/x-7z-compressed",
            ".tar": "application/x-tar",
            ".gz": "application/gzip",
            ".html": "text/html",
            ".htm": "text/html",
            ".xml": "text/xml",
            ".css": "text/css",
            ".js": "application/javascript",
            ".py": "text/x-python",
            ".java": "text/x-java-source",
            ".cpp": "text/x-c++src",
            ".c": "text/x-csrc",
            ".h": "text/x-chdr",
            ".hpp": "text/x-c++hdr",
        }
        media_type = media_types.get(ext.lower(), "application/octet-stream")

        # 创建自定义FileResponse，避免文件名编码问题
        response = StarletteFileResponse(path=normalized_path, media_type=media_type)

        # 正确处理中文文件名的HTTP头部设置
        # HTTP头部只能包含ASCII字符，所以需要对中文文件名进行编码
        try:
            # 尝试使用ASCII编码（适用于英文文件名）
            decoded_filename.encode("ascii")
            # 如果成功，直接使用简单格式
            response.headers["Content-Disposition"] = f'attachment; filename="{decoded_filename}"'
        except UnicodeEncodeError:
            # 如果包含非ASCII字符（如中文），使用RFC 2231格式
            encoded_filename = quote(decoded_filename.encode("utf-8"))
            response.headers["Content-Disposition"] = f"attachment; filename*=UTF-8''{encoded_filename}"

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载文件失败: {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"下载失败: {e}")


# =============================================================================
# === 查询分组 ===
# =============================================================================


@knowledge.post("/databases/{db_id}/query")
async def query_knowledge_base(
    db_id: str, query: str = Body(...), meta: dict = Body(...), current_user: User = Depends(get_admin_user)
):
    """查询知识库"""
    logger.debug(f"Query knowledge base {db_id}: {query}")
    try:
        result = await knowledge_base.aquery(query, db_id=db_id, **meta)
        return {"result": result, "status": "success"}
    except Exception as e:
        logger.error(f"知识库查询失败 {e}, {traceback.format_exc()}")
        return {"message": f"知识库查询失败: {e}", "status": "failed"}


@knowledge.post("/databases/{db_id}/query-test")
async def query_test(
    db_id: str, query: str = Body(...), meta: dict = Body(...), current_user: User = Depends(get_admin_user)
):
    """测试查询知识库"""
    logger.debug(f"Query test in {db_id}: {query}")
    try:
        result = await knowledge_base.aquery(query, db_id=db_id, **meta)
        return result
    except Exception as e:
        logger.error(f"测试查询失败 {e}, {traceback.format_exc()}")
        return {"message": f"测试查询失败: {e}", "status": "failed"}


@knowledge.get("/databases/{db_id}/query-params")
async def get_knowledge_base_query_params(db_id: str, current_user: User = Depends(get_admin_user)):
    """获取知识库类型特定的查询参数"""
    try:
        # 获取数据库信息
        db_info = knowledge_base.get_database_info(db_id)
        if not db_info:
            raise HTTPException(status_code=404, detail="Database not found")

        kb_type = db_info.get("kb_type", "lightrag")

        # 根据知识库类型返回不同的查询参数
        if kb_type == "lightrag":
            params = {
                "type": "lightrag",
                "options": [
                    {
                        "key": "mode",
                        "label": "检索模式",
                        "type": "select",
                        "default": "mix",
                        "options": [
                            {"value": "local", "label": "Local", "description": "上下文相关信息"},
                            {"value": "global", "label": "Global", "description": "全局知识"},
                            {"value": "hybrid", "label": "Hybrid", "description": "本地和全局混合"},
                            {"value": "naive", "label": "Naive", "description": "基本搜索"},
                            {"value": "mix", "label": "Mix", "description": "知识图谱和向量检索混合"},
                        ],
                    },
                    {
                        "key": "only_need_context",
                        "label": "只使用上下文",
                        "type": "boolean",
                        "default": True,
                        "description": "只返回上下文，不生成回答",
                    },
                    {
                        "key": "only_need_prompt",
                        "label": "只使用提示",
                        "type": "boolean",
                        "default": False,
                        "description": "只返回提示，不进行检索",
                    },
                    {
                        "key": "top_k",
                        "label": "TopK",
                        "type": "number",
                        "default": 10,
                        "min": 1,
                        "max": 100,
                        "description": "返回的最大结果数量",
                    },
                ],
            }
        elif kb_type == "chroma":
            params = {
                "type": "chroma",
                "options": [
                    {
                        "key": "top_k",
                        "label": "TopK",
                        "type": "number",
                        "default": 10,
                        "min": 1,
                        "max": 100,
                        "description": "返回的最大结果数量",
                    },
                    {
                        "key": "similarity_threshold",
                        "label": "相似度阈值",
                        "type": "number",
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.1,
                        "description": "过滤相似度低于此值的结果",
                    },
                    {
                        "key": "include_distances",
                        "label": "显示相似度",
                        "type": "boolean",
                        "default": True,
                        "description": "在结果中显示相似度分数",
                    },
                ],
            }
        elif kb_type == "milvus":
            params = {
                "type": "milvus",
                "options": [
                    {
                        "key": "top_k",
                        "label": "TopK",
                        "type": "number",
                        "default": 10,
                        "min": 1,
                        "max": 100,
                        "description": "返回的最大结果数量",
                    },
                    {
                        "key": "similarity_threshold",
                        "label": "相似度阈值",
                        "type": "number",
                        "default": 0.0,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.1,
                        "description": "过滤相似度低于此值的结果",
                    },
                    {
                        "key": "include_distances",
                        "label": "显示相似度",
                        "type": "boolean",
                        "default": True,
                        "description": "在结果中显示相似度分数",
                    },
                    {
                        "key": "metric_type",
                        "label": "距离度量类型",
                        "type": "select",
                        "default": "COSINE",
                        "options": [
                            {"value": "COSINE", "label": "余弦相似度", "description": "适合文本语义相似度"},
                            {"value": "L2", "label": "欧几里得距离", "description": "适合数值型数据"},
                            {"value": "IP", "label": "内积", "description": "适合标准化向量"},
                        ],
                        "description": "向量相似度计算方法",
                    },
                ],
            }
        else:
            # 未知类型，返回基本参数
            params = {
                "type": "unknown",
                "options": [
                    {
                        "key": "top_k",
                        "label": "TopK",
                        "type": "number",
                        "default": 10,
                        "min": 1,
                        "max": 100,
                        "description": "返回的最大结果数量",
                    }
                ],
            }

        return {"params": params, "message": "success"}

    except Exception as e:
        logger.error(f"获取知识库查询参数失败 {e}, {traceback.format_exc()}")
        return {"message": f"获取知识库查询参数失败 {e}", "params": {}}


# =============================================================================
# === 文件管理分组 ===
# =============================================================================


@knowledge.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    db_id: str | None = Query(None),
    allow_jsonl: bool = Query(False),
    current_user: User = Depends(get_admin_user),
):
    """上传文件"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No selected file")

    logger.debug(f"Received upload file with filename: {file.filename}")

    ext = os.path.splitext(file.filename)[1].lower()

    if ext == ".jsonl":
        if allow_jsonl is not True or db_id is not None:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    elif not is_supported_file_extension(file.filename):
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # 根据db_id获取上传路径，如果db_id为None则使用默认路径
    if db_id:
        upload_dir = knowledge_base.get_db_upload_path(db_id)
    else:
        upload_dir = os.path.join(config.save_dir, "database", "uploads")

    basename, ext = os.path.splitext(file.filename)
    filename = f"{basename}_{hashstr(basename, 4, with_salt=True)}{ext}".lower()
    file_path = os.path.join(upload_dir, filename)
    os.makedirs(upload_dir, exist_ok=True)

    file_bytes = await file.read()

    content_hash = calculate_content_hash(file_bytes)
    if knowledge_base.file_existed_in_db(db_id, content_hash):
        raise HTTPException(
            status_code=409,
            detail="数据库中已经存在了相同文件，File with the same content already exists in this database",
        )

    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    return {
        "message": "File successfully uploaded",
        "file_path": file_path,
        "db_id": db_id,
        "content_hash": content_hash,
    }


@knowledge.get("/files/supported-types")
async def get_supported_file_types(current_user: User = Depends(get_admin_user)):
    """获取当前支持的文件类型"""
    return {"message": "success", "file_types": sorted(SUPPORTED_FILE_EXTENSIONS)}


@knowledge.post("/files/markdown")
async def mark_it_down(file: UploadFile = File(...), current_user: User = Depends(get_admin_user)):
    """调用 src.knowledge.indexing 下面的 process_file_to_markdown 解析为 markdown，参数是文件，需要管理员权限"""
    try:
        content = await file.read()
        markdown_content = await process_file_to_markdown(content)
        return {"markdown_content": markdown_content, "message": "success"}
    except Exception as e:
        logger.error(f"文件解析失败 {e}, {traceback.format_exc()}")
        return {"message": f"文件解析失败 {e}", "markdown_content": ""}


# =============================================================================
# === MySQL 数据导入分组 ===
# =============================================================================


@knowledge.post("/mysql/preview")
async def preview_table_data(file: UploadFile = File(...), current_user: User = Depends(get_admin_user)):
    """预览 Excel/CSV 文件的全部数据"""
    import pandas as pd
    from io import BytesIO

    logger.debug(f"Preview table data from file: {file.filename}")

    try:
        # 检查文件类型
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}，仅支持 .csv, .xlsx, .xls")

        # 读取文件内容
        content = await file.read()
        file_buffer = BytesIO(content)

        # 根据文件类型加载数据
        if ext == ".csv":
            # 尝试多种编码
            try:
                df = pd.read_csv(file_buffer, encoding="utf-8")
            except UnicodeDecodeError:
                file_buffer.seek(0)
                try:
                    df = pd.read_csv(file_buffer, encoding="gbk")
                except UnicodeDecodeError:
                    file_buffer.seek(0)
                    df = pd.read_csv(file_buffer, encoding="latin1")
        elif ext in [".xlsx", ".xls"]:
            df = pd.read_excel(file_buffer)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

        # 替换 NaN 为 None（JSON 兼容）
        df = df.where(pd.notnull(df), None)

        # 获取列信息
        columns_info = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            columns_info.append({"name": col, "type": dtype})

        # 转换为字典列表（全部数据）
        data = df.to_dict(orient="records")

        return {
            "message": "success",
            "filename": file.filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": columns_info,
            "data": data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预览表格数据失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"预览表格数据失败: {e}")


@knowledge.post("/mysql/import")
async def import_to_mysql(
    file_path: str = Body(...),
    table_name: str = Body(...),
    create_table: bool = Body(True),
    drop_if_exists: bool = Body(False),
    batch_size: int = Body(1000),
    current_user: User = Depends(get_admin_user),
):
    """将上传的 Excel/CSV 文件导入到 MySQL"""
    import pandas as pd
    import pymysql
    from pathlib import Path

    logger.debug(f"Import file to MySQL: {file_path} -> {table_name}")

    try:
        # 验证文件存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")

        # 验证文件类型
        ext = Path(file_path).suffix.lower()
        if ext not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

        # 加载数据
        if ext == ".csv":
            try:
                df = pd.read_csv(file_path, encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding="gbk")
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding="latin1")
        else:
            df = pd.read_excel(file_path)

        # 处理列名（替换空格和特殊字符）
        df.columns = [col.replace(" ", "_").replace("-", "_") for col in df.columns]

        # 替换 NaN 为 None
        df = df.where(pd.notnull(df), None)

        # 连接 MySQL
        mysql_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "testdb"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "charset": "utf8mb4",
        }

        connection = pymysql.connect(**mysql_config)
        cursor = connection.cursor()

        try:
            # 检查表是否存在
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            table_exists = cursor.fetchone() is not None

            # 如果需要创建表
            if create_table:
                if table_exists and drop_if_exists:
                    logger.info(f"删除已存在的表: {table_name}")
                    cursor.execute(f"DROP TABLE `{table_name}`")
                    table_exists = False

                if not table_exists:
                    # 推断列类型
                    def infer_mysql_type(dtype, max_length=None):
                        dtype_str = str(dtype)
                        if "int" in dtype_str:
                            return "BIGINT"
                        elif "float" in dtype_str:
                            return "DOUBLE"
                        elif "bool" in dtype_str:
                            return "BOOLEAN"
                        elif "datetime" in dtype_str:
                            return "DATETIME"
                        elif "date" in dtype_str:
                            return "DATE"
                        else:
                            if max_length and max_length < 255:
                                return f"VARCHAR({max(255, max_length + 50)})"
                            else:
                                return "TEXT"

                    # 构建列定义
                    columns = []
                    for col in df.columns:
                        dtype = df[col].dtype
                        max_length = None
                        if dtype == "object":
                            max_length = df[col].astype(str).str.len().max()
                        mysql_type = infer_mysql_type(dtype, max_length)
                        columns.append(f"`{col}` {mysql_type}")

                    # 添加自增主键
                    columns.insert(0, "`id` BIGINT AUTO_INCREMENT PRIMARY KEY")

                    # 创建表
                    create_sql = f"""
                    CREATE TABLE `{table_name}` (
                        {', '.join(columns)}
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    """
                    cursor.execute(create_sql)
                    connection.commit()
                    logger.info(f"✓ 表 {table_name} 创建成功")

            elif not table_exists:
                raise HTTPException(status_code=400, detail=f"表 {table_name} 不存在，请启用 create_table 选项")

            # 导入数据
            columns_str = ", ".join([f"`{col}`" for col in df.columns])
            placeholders = ", ".join(["%s"] * len(df.columns))
            insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"

            total_rows = len(df)
            inserted = 0

            for i in range(0, total_rows, batch_size):
                batch = df.iloc[i : i + batch_size]
                data = [tuple(row) for row in batch.values]
                cursor.executemany(insert_sql, data)
                connection.commit()
                inserted += len(batch)
                logger.info(f"已导入 {inserted}/{total_rows} 行 ({inserted/total_rows*100:.1f}%)")

            # 验证导入结果
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            count = cursor.fetchone()[0]

            cursor.close()
            connection.close()

            return {
                "message": "导入成功",
                "status": "success",
                "table_name": table_name,
                "total_rows": total_rows,
                "inserted_rows": inserted,
                "final_count": count,
            }

        except Exception as e:
            connection.rollback()
            cursor.close()
            connection.close()
            raise HTTPException(status_code=500, detail=f"数据导入失败: {e}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入到 MySQL 失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"导入失败: {e}")


@knowledge.get("/mysql/tables")
async def get_mysql_tables(current_user: User = Depends(get_admin_user)):
    """获取 MySQL 数据库中的所有表及其统计信息"""
    import pymysql
    from datetime import datetime

    logger.debug("Getting MySQL tables list")

    try:
        # 连接 MySQL
        mysql_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "testdb"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "charset": "utf8mb4",
        }

        connection = pymysql.connect(**mysql_config)
        cursor = connection.cursor()

        # 获取所有表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        # 获取每个表的详细信息
        table_list = []
        for (table_name,) in tables:
            # 获取行数
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]

            # 获取列数和列信息
            cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
            columns = cursor.fetchall()
            column_count = len(columns)

            # 获取表创建时间
            cursor.execute(f"SHOW TABLE STATUS LIKE '{table_name}'")
            table_status = cursor.fetchone()
            create_time = table_status[11] if table_status and len(table_status) > 11 else None  # Create_time

            table_list.append(
                {
                    "name": table_name,
                    "row_count": row_count,
                    "column_count": column_count,
                    "create_time": create_time.isoformat() if create_time else None,
                    "columns": [col[0] for col in columns],  # 列名列表
                }
            )

        cursor.close()
        connection.close()

        return {"message": "success", "tables": table_list, "total": len(table_list)}

    except Exception as e:
        logger.error(f"获取 MySQL 表列表失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {e}")


@knowledge.get("/mysql/tables/{table_name}")
async def get_table_info(table_name: str, current_user: User = Depends(get_admin_user)):
    """获取指定表的详细信息（表结构）"""
    import pymysql

    logger.debug(f"Getting table info for {table_name}")

    try:
        # 连接 MySQL
        mysql_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "testdb"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "charset": "utf8mb4",
        }

        connection = pymysql.connect(**mysql_config)
        cursor = connection.cursor()

        # 检查表是否存在
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")

        # 获取表结构
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns_raw = cursor.fetchall()
        columns = [
            {
                "name": col[0],
                "type": col[1],
                "null": col[2] == "YES",
                "key": col[3],
                "default": col[4],
                "extra": col[5],
            }
            for col in columns_raw
        ]

        # 获取行数
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        row_count = cursor.fetchone()[0]

        # 获取表状态信息
        cursor.execute(f"SHOW TABLE STATUS LIKE '{table_name}'")
        table_status = cursor.fetchone()
        create_time = table_status[11] if table_status and len(table_status) > 11 else None
        engine = table_status[1] if table_status and len(table_status) > 1 else None
        collation = table_status[14] if table_status and len(table_status) > 14 else None

        cursor.close()
        connection.close()

        return {
            "message": "success",
            "table_name": table_name,
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns,
            "create_time": create_time.isoformat() if create_time else None,
            "engine": engine,
            "collation": collation,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取表信息失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取表信息失败: {e}")


@knowledge.get("/mysql/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_admin_user),
):
    """获取表数据（分页）"""
    import pymysql

    logger.debug(f"Getting data from table {table_name}, offset={offset}, limit={limit}")

    try:
        # 连接 MySQL
        mysql_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "testdb"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "charset": "utf8mb4",
        }

        connection = pymysql.connect(**mysql_config)
        cursor = connection.cursor()

        # 检查表是否存在
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")

        # 获取列信息
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns_info = cursor.fetchall()
        column_names = [col[0] for col in columns_info]

        # 获取总行数
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        total_count = cursor.fetchone()[0]

        # 获取数据
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {limit} OFFSET {offset}")
        rows = cursor.fetchall()

        # 转换为字典列表
        data = []
        for row in rows:
            row_dict = {}
            for i, col_name in enumerate(column_names):
                value = row[i]
                # 处理日期时间类型
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                row_dict[col_name] = value
            data.append(row_dict)

        cursor.close()
        connection.close()

        return {
            "message": "success",
            "table_name": table_name,
            "columns": column_names,
            "data": data,
            "total": total_count,
            "offset": offset,
            "limit": limit,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取表数据失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取表数据失败: {e}")


@knowledge.delete("/mysql/tables/{table_name}")
async def delete_table(table_name: str, current_user: User = Depends(get_admin_user)):
    """删除 MySQL 表"""
    import pymysql

    logger.debug(f"Deleting table {table_name}")

    try:
        # 连接 MySQL
        mysql_config = {
            "host": os.getenv("MYSQL_HOST", "localhost"),
            "user": os.getenv("MYSQL_USER", "root"),
            "password": os.getenv("MYSQL_PASSWORD", ""),
            "database": os.getenv("MYSQL_DATABASE", "testdb"),
            "port": int(os.getenv("MYSQL_PORT", "3306")),
            "charset": "utf8mb4",
        }

        connection = pymysql.connect(**mysql_config)
        cursor = connection.cursor()

        # 检查表是否存在
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")

        # 删除表
        cursor.execute(f"DROP TABLE `{table_name}`")
        connection.commit()

        cursor.close()
        connection.close()

        return {"message": f"表 {table_name} 已成功删除", "status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除表失败 {e}, {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"删除表失败: {e}")


# =============================================================================
# === 知识库类型分组 ===
# =============================================================================


@knowledge.get("/types")
async def get_knowledge_base_types(current_user: User = Depends(get_admin_user)):
    """获取支持的知识库类型"""
    try:
        kb_types = knowledge_base.get_supported_kb_types()
        return {"kb_types": kb_types, "message": "success"}
    except Exception as e:
        logger.error(f"获取知识库类型失败 {e}, {traceback.format_exc()}")
        return {"message": f"获取知识库类型失败 {e}", "kb_types": {}}


@knowledge.get("/stats")
async def get_knowledge_base_statistics(current_user: User = Depends(get_admin_user)):
    """获取知识库统计信息"""
    try:
        stats = knowledge_base.get_statistics()
        return {"stats": stats, "message": "success"}
    except Exception as e:
        logger.error(f"获取知识库统计失败 {e}, {traceback.format_exc()}")
        return {"message": f"获取知识库统计失败 {e}", "stats": {}}


# =============================================================================
# === Embedding模型状态检查分组 ===
# =============================================================================


@knowledge.get("/embedding-models/{model_id}/status")
async def get_embedding_model_status(model_id: str, current_user: User = Depends(get_admin_user)):
    """获取指定embedding模型的状态"""
    logger.debug(f"Checking embedding model status: {model_id}")
    try:
        status = await test_embedding_model_status(model_id)
        return {"status": status, "message": "success"}
    except Exception as e:
        logger.error(f"获取embedding模型状态失败 {model_id}: {e}, {traceback.format_exc()}")
        return {
            "message": f"获取embedding模型状态失败: {e}",
            "status": {"model_id": model_id, "status": "error", "message": str(e)},
        }


@knowledge.get("/embedding-models/status")
async def get_all_embedding_models_status(current_user: User = Depends(get_admin_user)):
    """获取所有embedding模型的状态"""
    logger.debug("Checking all embedding models status")
    try:
        status = await test_all_embedding_models_status()
        return {"status": status, "message": "success"}
    except Exception as e:
        logger.error(f"获取所有embedding模型状态失败: {e}, {traceback.format_exc()}")
        return {"message": f"获取所有embedding模型状态失败: {e}", "status": {"models": {}, "total": 0, "available": 0}}
