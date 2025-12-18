"""
MinIO 存储服务
提供高层次的文件存储 API
"""

import os
import uuid
from pathlib import Path

from src.storage.minio import MinIOClient, StorageError, get_minio_client
from src.utils import logger


class MinioStorage:
    """
    MinIO 存储服务类
    提供简化的文件上传和管理接口
    """

    # 公开访问的存储桶列表
    PUBLIC_BUCKETS = {"temp-ocr", "generated-images", "avatar"}

    def __init__(self, client: MinIOClient = None):
        """
        初始化 MinIO 存储服务

        Args:
            client: MinIO 客户端实例，如果为 None 则使用默认客户端
        """
        self.client = client or get_minio_client()

    def upload_file_and_get_url(self, file_path: str, bucket_name: str = "temp-ocr", object_name: str = None) -> str:
        """
        上传文件到 MinIO 并返回公开访问 URL

        Args:
            file_path: 本地文件路径
            bucket_name: 存储桶名称，默认 "temp-ocr"
            object_name: 对象名称（MinIO 中的文件名），如果为 None 则自动生成

        Returns:
            str: 文件的公开访问 URL

        Raises:
            StorageError: 上传失败时抛出
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                raise StorageError(f"文件不存在: {file_path}")

            # 如果未指定对象名称，则生成唯一名称
            if object_name is None:
                original_name = os.path.basename(file_path)
                object_name = self._generate_unique_object_name(original_name)

            # 确保存储桶存在且配置为公开访问
            self._ensure_public_bucket(bucket_name)

            # 上传文件
            result = self.client.upload_file_from_path(bucket_name, object_name, file_path)

            logger.info(f"文件上传成功: {file_path} -> {result.url}")
            return result.url

        except StorageError:
            raise
        except Exception as e:
            error_msg = f"上传文件失败: {file_path} - {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)

    def upload_bytes_and_get_url(
        self, data: bytes, file_name: str, bucket_name: str = "temp-ocr", content_type: str = None
    ) -> str:
        """
        上传字节数据到 MinIO 并返回公开访问 URL

        Args:
            data: 文件字节数据
            file_name: 文件名（用于生成对象名称和推断 MIME 类型）
            bucket_name: 存储桶名称，默认 "temp-ocr"
            content_type: MIME 类型，如果为 None 则自动推断

        Returns:
            str: 文件的公开访问 URL

        Raises:
            StorageError: 上传失败时抛出
        """
        try:
            # 生成唯一对象名称
            object_name = self._generate_unique_object_name(file_name)

            # 如果未指定 content_type，则自动推断
            if content_type is None:
                content_type = self.client._guess_content_type(object_name)

            # 确保存储桶存在且配置为公开访问
            self._ensure_public_bucket(bucket_name)

            # 上传数据
            result = self.client.upload_file(bucket_name, object_name, data, content_type)

            logger.info(f"数据上传成功: {file_name} ({len(data)} bytes) -> {result.url}")
            return result.url

        except StorageError:
            raise
        except Exception as e:
            error_msg = f"上传数据失败: {file_name} - {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)

    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """
        删除文件

        Args:
            bucket_name: 存储桶名称
            object_name: 对象名称

        Returns:
            bool: 删除是否成功
        """
        try:
            return self.client.delete_file(bucket_name, object_name)
        except Exception as e:
            logger.error(f"删除文件失败: {bucket_name}/{object_name} - {str(e)}")
            return False

    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        检查文件是否存在

        Args:
            bucket_name: 存储桶名称
            object_name: 对象名称

        Returns:
            bool: 文件是否存在
        """
        try:
            return self.client.file_exists(bucket_name, object_name)
        except Exception as e:
            logger.error(f"检查文件存在性失败: {bucket_name}/{object_name} - {str(e)}")
            return False

    def _generate_unique_object_name(self, original_name: str) -> str:
        """
        生成唯一的对象名称

        Args:
            original_name: 原始文件名

        Returns:
            str: 唯一的对象名称
        """
        # 获取文件扩展名
        path = Path(original_name)
        extension = path.suffix

        # 生成唯一 ID
        unique_id = uuid.uuid4().hex[:12]

        # 组合：唯一ID_原始名称（保留扩展名）
        stem = path.stem[:50]  # 限制原始名称长度
        return f"{unique_id}_{stem}{extension}"

    def _ensure_public_bucket(self, bucket_name: str) -> None:
        """
        确保存储桶存在并配置为公开访问（如果在公开桶列表中）

        Args:
            bucket_name: 存储桶名称

        Raises:
            StorageError: 创建或配置失败时抛出
        """
        try:
            # 如果是公开桶，将其添加到客户端的公开桶列表
            if bucket_name in self.PUBLIC_BUCKETS:
                if bucket_name not in self.client.PUBLIC_READ_BUCKETS:
                    self.client.PUBLIC_READ_BUCKETS.add(bucket_name)

            # 确保桶存在（会自动配置公开访问）
            self.client.ensure_bucket_exists(bucket_name)

        except Exception as e:
            error_msg = f"确保存储桶存在失败: {bucket_name} - {str(e)}"
            logger.error(error_msg)
            raise StorageError(error_msg)


# 全局实例
_default_storage = None


def get_minio_storage() -> MinioStorage:
    """获取 MinIO 存储服务的全局实例"""
    global _default_storage
    if _default_storage is None:
        _default_storage = MinioStorage()
    return _default_storage
