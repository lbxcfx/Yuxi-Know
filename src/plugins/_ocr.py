import os
import time
import uuid
from argparse import ArgumentParser
from collections import defaultdict

import fitz  # fitz就是pip install PyMuPDF
import numpy as np  # Added import for numpy
from PIL import Image
from rapidocr_onnxruntime import RapidOCR
from tqdm import tqdm

from src.utils import logger

GOLBAL_STATE = {}

# OCR服务监控统计
OCR_STATS = {"requests": defaultdict(int), "failures": defaultdict(int), "service_status": defaultdict(str)}


def log_ocr_request(service_name: str, file_path: str, success: bool, processing_time: float, error_msg: str = None):
    """记录OCR请求统计信息"""
    # 更新统计
    OCR_STATS["requests"][service_name] += 1

    if not success:
        OCR_STATS["failures"][service_name] += 1
        OCR_STATS["service_status"][service_name] = "error"
        logger.error(f"OCR失败 - {service_name}: {os.path.basename(file_path)} - {error_msg}")
    else:
        OCR_STATS["service_status"][service_name] = "healthy"
        logger.info(f"OCR成功 - {service_name}: {os.path.basename(file_path)}")


def get_ocr_stats():
    """获取OCR服务统计信息"""
    stats = {}
    for service in OCR_STATS["requests"]:
        success_count = OCR_STATS["requests"][service] - OCR_STATS["failures"][service]
        success_rate = (success_count / OCR_STATS["requests"][service]) if OCR_STATS["requests"][service] > 0 else 0

        stats[service] = {
            "total_requests": OCR_STATS["requests"][service],
            "success_count": success_count,
            "failure_count": OCR_STATS["failures"][service],
            "success_rate": f"{success_rate:.2%}",
            "status": OCR_STATS["service_status"][service],
        }

    return stats


class OCRServiceException(Exception):
    """OCR服务异常"""

    def __init__(self, message, service_name=None, status_code=None):
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code


class OCRPlugin:
    """OCR 插件"""

    def __init__(self, **kwargs):
        self.ocr = None
        self.det_box_thresh = kwargs.get("det_box_thresh", 0.3)
        self.model_dir_root = (
            os.getenv("MODEL_DIR") if not os.getenv("RUNNING_IN_DOCKER") else os.getenv("MODEL_DIR_IN_DOCKER")
        )

    def _check_rapid_ocr_availability(self):
        """检查RapidOCR模型是否可用"""
        try:
            model_dir = os.path.join(self.model_dir_root, "SWHL/RapidOCR")
            det_model_dir = os.path.join(model_dir, "PP-OCRv4/ch_PP-OCRv4_det_infer.onnx")
            rec_model_dir = os.path.join(model_dir, "PP-OCRv4/ch_PP-OCRv4_rec_infer.onnx")

            if not os.path.exists(model_dir):
                raise OCRServiceException(
                    f"模型目录不存在: {model_dir}。请下载 SWHL/RapidOCR 模型", "rapid_ocr", "model_not_found"
                )

            if not os.path.exists(det_model_dir) or not os.path.exists(rec_model_dir):
                raise OCRServiceException(
                    f"模型文件缺失。请确认模型文件完整: {det_model_dir}, {rec_model_dir}",
                    "rapid_ocr",
                    "model_incomplete",
                )

            return True

        except Exception as e:
            if isinstance(e, OCRServiceException):
                raise
            else:
                raise OCRServiceException(f"RapidOCR模型检查失败: {str(e)}", "rapid_ocr", "check_failed")

    def load_model(self):
        """加载 OCR 模型"""
        logger.info("加载 OCR 模型，仅在第一次调用时加载")

        # 先检查模型可用性
        self._check_rapid_ocr_availability()

        model_dir = os.path.join(self.model_dir_root, "SWHL/RapidOCR")
        det_model_dir = os.path.join(model_dir, "PP-OCRv4/ch_PP-OCRv4_det_infer.onnx")
        rec_model_dir = os.path.join(model_dir, "PP-OCRv4/ch_PP-OCRv4_rec_infer.onnx")

        try:
            self.ocr = RapidOCR(det_box_thresh=0.3, det_model_path=det_model_dir, rec_model_path=rec_model_dir)
            logger.info(f"OCR Plugin for det_box_thresh = {self.det_box_thresh} loaded.")
        except Exception as e:
            raise OCRServiceException(f"RapidOCR模型加载失败: {str(e)}", "rapid_ocr", "load_failed")

    def process_image(self, image, params=None):
        """
        对单张图像执行OCR并提取文本

        Args:
            image: 图像数据，支持多种格式：
                  - str: 图像文件路径
                  - PIL.Image: PIL图像对象
                  - numpy.ndarray: numpy图像数组
            params: 参数
        Returns:
            str: 提取的文本内容
        """
        # 确保模型已加载
        if self.ocr is None:
            self.load_model()

        # 处理不同类型的输入图像
        try:
            if isinstance(image, str):
                # 图像路径直接传递给OCR处理
                image_path = image
                is_temp_file = False
            else:
                # 创建临时文件
                is_temp_file = True
                image_path = self._create_temp_image_file(image)

            # 执行 OCR
            start_time = time.time()
            result, _ = self.ocr(image_path)
            processing_time = time.time() - start_time

            # 清理临时文件
            if is_temp_file and os.path.exists(image_path):
                os.remove(image_path)

            # 提取文本
            if result:
                text = "\n".join([line[1] for line in result])
                log_ocr_request("rapid_ocr", image_path, True, processing_time)
                return text
            else:
                log_ocr_request("rapid_ocr", image_path, False, processing_time, "OCR未能识别出文本内容")
                return ""

        except Exception as e:
            error_msg = f"OCR处理失败: {str(e)}"
            log_ocr_request("rapid_ocr", image_path, False, 0, error_msg)
            logger.error(error_msg)
            raise OCRServiceException(error_msg, "rapid_ocr", "processing_failed")

    def _create_temp_image_file(self, image):
        """
        将图像数据保存为临时文件

        Args:
            image: PIL.Image或numpy.ndarray格式的图像数据

        Returns:
            str: 临时文件路径
        """
        # 为临时文件创建目录（如果不存在）
        tmp_dir = os.path.join(os.getcwd(), "tmp")
        os.makedirs(tmp_dir, exist_ok=True)

        # 生成临时文件路径
        temp_filename = f"ocr_temp_{uuid.uuid4().hex[:8]}.png"
        image_path = os.path.join(tmp_dir, temp_filename)

        # 根据图像类型保存文件
        if isinstance(image, Image.Image):
            # 保存PIL图像对象到临时文件
            image.save(image_path)
        elif isinstance(image, np.ndarray):
            # 将numpy数组转换为PIL图像并保存
            Image.fromarray(image).save(image_path)
        else:
            raise ValueError("不支持的图像类型，必须是PIL.Image或numpy数组")

        return image_path

    def process_pdf(self, pdf_path, params=None):
        """
        处理PDF文件并提取文本
        :param pdf_path: PDF文件路径
        :param params: 参数
        :return: 提取的文本
        """

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        try:
            images = []

            pdfDoc = fitz.open(pdf_path)
            totalPage = pdfDoc.page_count
            for pg in tqdm(range(totalPage), desc="to images", ncols=100):
                page = pdfDoc[pg]
                rotate, zoom_x, zoom_y = 0, 2, 2
                mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotate)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(img_pil)

            # 处理每个图像并合并文本
            all_text = []
            for img_path in tqdm(images, desc="to txt", ncols=100):
                text = self.process_image(img_path)
                all_text.append(text)

            logger.debug(f"PDF OCR result: {all_text[:50]}(...) total {len(all_text)} pages.")
            return "\n\n".join(all_text)

        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            return ""

    def process_file_qwen_vl(self, file_path, params=None):
        """
        使用通义千问 VL 模型处理图片和 PDF
        支持通过 base64 编码直接发送文件内容

        :param file_path: 文件路径（支持图片和 PDF）
        :param params: 参数字典，可包含 prompt（默认为 OCR 提示）
        :return: 提取的文本
        """
        import base64
        from openai import OpenAI

        api_key = os.getenv("DASHSCOPE_API_KEY", "")
        if not api_key:
            raise OCRServiceException(
                "未配置 DASHSCOPE_API_KEY，无法使用通义千问 VL 模型", "qwen_vl", "missing_api_key"
            )

        try:
            start_time = time.time()

            # 如果是 PDF，先转换为图片
            if file_path.lower().endswith('.pdf'):
                images = self._pdf_to_images(file_path)
                if not images:
                    raise OCRServiceException("PDF 转换为图片失败", "qwen_vl", "pdf_conversion_failed")
            else:
                # 直接读取图片
                images = [file_path]

            # 处理所有图片
            all_text = []
            for img_path in tqdm(images, desc="Processing images with Qwen-VL", ncols=100):
                text = self._process_image_qwen_vl(img_path, api_key, params)
                if text:
                    all_text.append(text)

            result_text = "\n\n".join(all_text)
            processing_time = time.time() - start_time

            log_ocr_request("qwen_vl", file_path, True, processing_time)
            logger.info(f"✓ Qwen-VL OCR 处理成功，提取 {len(result_text)} 个字符，耗时 {processing_time:.2f}s")

            return result_text

        except OCRServiceException:
            raise
        except Exception as e:
            processing_time = time.time() - start_time if 'start_time' in locals() else 0
            error_msg = f"Qwen-VL OCR 处理失败: {str(e)}"
            log_ocr_request("qwen_vl", file_path, False, processing_time, error_msg)
            raise OCRServiceException(error_msg, "qwen_vl", "processing_failed")

    def _process_image_qwen_vl(self, image_path, api_key, params=None):
        """
        使用 Qwen-VL 处理单张图片

        :param image_path: 图片路径
        :param api_key: API Key
        :param params: 参数字典
        :return: 提取的文本
        """
        import base64
        from openai import OpenAI

        try:
            # 读取图片并转换为 base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")

            # 判断图片格式
            ext = os.path.splitext(image_path)[1].lower()
            image_format_map = {
                '.png': 'png',
                '.jpg': 'jpeg',
                '.jpeg': 'jpeg',
                '.webp': 'webp',
                '.bmp': 'png',  # BMP 转换为 PNG 格式
                '.tiff': 'png',
                '.tif': 'png'
            }
            image_format = image_format_map.get(ext, 'png')

            # 获取自定义提示词，默认使用 OCR 提示
            prompt = params.get("prompt") if params else None
            if not prompt:
                prompt = (
                    "请识别图片中的所有文字内容，按原文的顺序和格式输出。"
                    "如果图片中有表格，请保持表格结构。"
                    "只输出识别的文字，不要添加任何解释或描述。"
                )

            # 创建 OpenAI 客户端
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            )

            # 调用 API
            completion = client.chat.completions.create(
                model="qwen-vl-plus",  # 使用 qwen-vl-plus 模型
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/{image_format};base64,{base64_image}"},
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            )

            # 提取结果
            text = completion.choices[0].message.content
            return text

        except Exception as e:
            logger.error(f"Qwen-VL 处理图片失败: {image_path} - {str(e)}")
            raise OCRServiceException(f"Qwen-VL 处理图片失败: {str(e)}", "qwen_vl", "api_error")

    def _pdf_to_images(self, pdf_path):
        """
        将 PDF 转换为图片列表

        :param pdf_path: PDF 文件路径
        :return: 图片路径列表
        """
        try:
            images = []
            pdfDoc = fitz.open(pdf_path)
            totalPage = pdfDoc.page_count

            # 创建临时目录
            tmp_dir = os.path.join(os.getcwd(), "tmp", "pdf_images")
            os.makedirs(tmp_dir, exist_ok=True)

            for pg in range(totalPage):
                page = pdfDoc[pg]
                # 使用较高的分辨率以提高 OCR 准确率
                rotate, zoom_x, zoom_y = 0, 2, 2
                mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotate)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                # 保存为临时图片
                img_path = os.path.join(tmp_dir, f"page_{pg}.png")
                img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img_pil.save(img_path)
                images.append(img_path)

            logger.info(f"PDF 转换为 {len(images)} 张图片")
            return images

        except Exception as e:
            logger.error(f"PDF 转换为图片失败: {str(e)}")
            return []

    def _process_file_mineru_api(self, file_path, api_key, params=None):
        """
        使用 MinerU 官方 API 处理文件
        API 文档: https://mineru.net

        新版 API 流程:
        1. 提交任务，获取 task_id
        2. 轮询任务状态
        3. 任务完成后下载 ZIP 文件
        4. 从 ZIP 中提取 markdown 文件
        """
        import requests
        import json
        import zipfile
        import io

        mineru_api_url = os.getenv("MINERU_API_URL", "https://mineru.net/api/v4/extract/task")

        try:
            start_time = time.time()

            # 1. 准备文件 URL
            # 如果文件已经是 URL，直接使用
            if file_path.startswith("http://") or file_path.startswith("https://"):
                file_url = file_path
            else:
                # 尝试上传到 MinIO
                try:
                    from src.storage.minio_storage import MinioStorage
                    minio = MinioStorage()
                    file_url = minio.upload_file_and_get_url(file_path, bucket_name="temp-ocr")
                    logger.info(f"文件已上传到 MinIO: {file_url}")
                except Exception as e:
                    logger.warning(f"MinIO 上传失败: {e}，文件需要公开 URL 才能使用 MinerU API")
                    raise OCRServiceException(
                        "MinerU API 需要文件公开 URL，但 MinIO 上传失败", "mineru_api", "upload_failed"
                    )

            logger.info(f"准备使用 MinerU API 处理文件: {file_url}")

            # 2. 调用 MinerU API 提交任务
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            data = {
                "url": file_url,
                "is_ocr": params.get("is_ocr", True) if params else True,
                "enable_formula": params.get("enable_formula", False) if params else False,
            }

            logger.debug(f"调用 MinerU API: {mineru_api_url}")
            response = requests.post(mineru_api_url, headers=headers, json=data, timeout=60)

            if response.status_code != 200:
                error_msg = f"MinerU API 调用失败: HTTP {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg = f"{error_msg} - {error_detail}"
                except:
                    error_msg = f"{error_msg} - {response.text}"

                raise OCRServiceException(error_msg, "mineru_api", "api_error")

            # 3. 解析响应，获取任务 ID
            result = response.json()

            # 新版 API: code=0 表示成功，旧版 API: code=200
            if result.get("code") not in [0, 200]:
                error_msg_raw = result.get('msg', result.get('message', 'Unknown error'))
                error_msg = f"MinerU API 返回错误: {error_msg_raw}"

                # 特殊错误提示
                if "failed to read file" in error_msg_raw.lower() or "-60003" in str(result.get("code")):
                    error_msg += "\n提示: MinerU API 无法访问文件 URL，请确保文件 URL 可从公网访问。"
                    error_msg += "\n本地 MinIO (localhost) 无法被 MinerU API 访问，建议使用公网对象存储或本地 MinerU 服务。"

                raise OCRServiceException(error_msg, "mineru_api", "api_error")

            data_result = result.get("data", {})

            # 检查是否是新版 API（返回 task_id）
            if isinstance(data_result, dict) and "task_id" in data_result:
                task_id = data_result["task_id"]
                logger.info(f"获取到任务 ID: {task_id}")

                # 4. 轮询任务状态
                query_url = f"https://mineru.net/api/v4/extract/task/{task_id}"
                max_retries = 60  # 最多等待 5 分钟
                retry_interval = 5

                for i in range(max_retries):
                    time.sleep(retry_interval)

                    query_response = requests.get(query_url, headers=headers, timeout=30)
                    if query_response.status_code != 200:
                        logger.warning(f"查询任务状态失败: {query_response.status_code}")
                        continue

                    task_result = query_response.json()
                    if task_result.get("code") == 0:
                        task_data = task_result.get("data", {})
                        state = task_data.get("state")

                        if state == "done":
                            # 任务完成
                            data_url = task_data.get("full_zip_url")
                            if data_url:
                                logger.info(f"任务完成，获取到结果 URL: {data_url}")
                                break
                            else:
                                raise OCRServiceException("任务完成但未返回结果 URL", "mineru_api", "no_data")
                        elif state == "failed" or state == "error":
                            err_msg = task_data.get("err_msg", "Unknown error")
                            raise OCRServiceException(f"任务失败: {err_msg}", "mineru_api", "task_failed")
                        else:
                            logger.debug(f"任务状态: {state} (第 {i+1}/{max_retries} 次查询)")
                else:
                    raise OCRServiceException(
                        f"任务超时，未能在 {max_retries * retry_interval} 秒内完成", "mineru_api", "timeout"
                    )
            else:
                # 旧版 API，直接返回 URL
                if isinstance(data_result, str):
                    data_url = data_result
                else:
                    raise OCRServiceException("API 返回数据格式异常", "mineru_api", "invalid_format")

            # 5. 下载结果
            logger.info(f"下载处理结果: {data_url}")
            result_response = requests.get(data_url, timeout=120)
            if result_response.status_code != 200:
                raise OCRServiceException(
                    f"下载 MinerU 结果失败: HTTP {result_response.status_code}", "mineru_api", "download_error"
                )

            # 6. 解析结果
            if data_url.endswith('.zip'):
                # ZIP 文件，需要解压并提取 markdown
                logger.debug(f"解压 ZIP 文件 ({len(result_response.content) / 1024:.2f} KB)")

                zip_file = zipfile.ZipFile(io.BytesIO(result_response.content))
                md_files = [f for f in zip_file.namelist() if f.endswith('.md')]

                if not md_files:
                    raise OCRServiceException("ZIP 文件中未找到 markdown 文件", "mineru_api", "no_markdown")

                # 读取第一个 markdown 文件（通常是 full.md）
                md_file = md_files[0]
                logger.debug(f"提取 markdown 文件: {md_file}")

                with zip_file.open(md_file) as f:
                    text = f.read().decode('utf-8')
            else:
                # 直接是文本内容
                text = result_response.text

            processing_time = time.time() - start_time
            log_ocr_request("mineru_api", file_path, True, processing_time)

            logger.info(f"✓ MinerU API 处理成功，提取 {len(text)} 个字符，耗时 {processing_time:.2f}s")
            logger.debug(f"MinerU API result preview: {text[:200]}...")

            return text

        except OCRServiceException:
            raise
        except Exception as e:
            processing_time = time.time() - start_time if 'start_time' in locals() else 0
            error_msg = f"MinerU API 处理失败: {str(e)}"
            log_ocr_request("mineru_api", file_path, False, processing_time, error_msg)
            raise OCRServiceException(error_msg, "mineru_api", "processing_failed")

    def _process_file_mineru_local(self, file_path, params=None):
        """
        使用本地 MinerU 服务处理文件
        """
        import requests
        from .mineru import parse_doc

        mineru_ocr_uri = os.getenv("MINERU_OCR_URI", "http://localhost:30000")
        mineru_ocr_uri_health = f"{mineru_ocr_uri}/health"

        try:
            # 健康检查
            health_check_response = requests.get(mineru_ocr_uri_health, timeout=5)
            if health_check_response.status_code != 200:
                error_detail = "Unknown error"
                try:
                    error_detail = health_check_response.json()
                except Exception:
                    error_detail = health_check_response.text

                raise OCRServiceException(
                    f"MinerU 本地服务健康检查失败: {error_detail}", "mineru_local", "health_check_failed"
                )

        except Exception as e:
            if isinstance(e, OCRServiceException):
                raise
            raise OCRServiceException(f"MinerU 本地服务检查失败: {str(e)}", "mineru_local", "service_error")

        try:
            start_time = time.time()
            file_path_list = [file_path]
            output_dir = os.path.join(os.getcwd(), "tmp", "mineru_ocr")

            text = parse_doc(file_path_list, output_dir, backend="vlm-sglang-client", server_url=mineru_ocr_uri)[0]

            processing_time = time.time() - start_time
            log_ocr_request("mineru_local", file_path, True, processing_time)

            logger.debug(f"MinerU 本地服务处理结果: {text[:50]}(...) 共 {len(text)} 个字符")
            return text

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"MinerU 本地服务处理失败: {str(e)}"
            log_ocr_request("mineru_local", file_path, False, processing_time, error_msg)

            raise OCRServiceException(error_msg, "mineru_local", "processing_failed")

    def process_file_paddlex(self, pdf_path, params=None):
        """
        使用Paddlex OCR处理PDF文件
        :param pdf_path: PDF文件路径
        :param params: 参数
        :return: 提取的文本
        """
        from .paddlex import analyze_document, check_paddlex_health

        paddlex_uri = os.getenv("PADDLEX_URI", "http://localhost:8080")

        try:
            # 健康检查
            health_check_response = check_paddlex_health(paddlex_uri)
            if not health_check_response.ok:
                error_detail = "Unknown error"
                try:
                    error_detail = health_check_response.json()
                except Exception:
                    error_detail = health_check_response.text

                raise OCRServiceException(
                    f"PaddleX OCR服务健康检查失败: {error_detail}", "paddlex_ocr", "health_check_failed"
                )
        except Exception as e:
            if isinstance(e, OCRServiceException):
                raise
            raise OCRServiceException(f"PaddleX OCR服务检查失败: {str(e)}", "paddlex_ocr", "service_error")

        try:
            start_time = time.time()
            result = analyze_document(pdf_path, base_url=paddlex_uri)
            processing_time = time.time() - start_time

            if not result["success"]:
                error_msg = f"PaddleX OCR处理失败: {result['error']}"
                log_ocr_request("paddlex_ocr", pdf_path, False, processing_time, error_msg)

                raise OCRServiceException(error_msg, "paddlex_ocr", "processing_failed")

            log_ocr_request("paddlex_ocr", pdf_path, True, processing_time)
            return result["full_text"]

        except Exception as e:
            if isinstance(e, OCRServiceException):
                raise
            processing_time = time.time() - start_time if "start_time" in locals() else 0
            error_msg = f"PaddleX OCR处理失败: {str(e)}"
            log_ocr_request("paddlex_ocr", pdf_path, False, processing_time, error_msg)

            raise OCRServiceException(error_msg, "paddlex_ocr", "processing_failed")


def get_state(task_id):
    return GOLBAL_STATE.get(task_id, {})


def plainreader(file_path):
    """读取普通文本文件并返回text文本"""
    assert os.path.exists(file_path), "File not found"

    with open(file_path) as f:
        text = f.read()
    return text


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--pdf-path", type=str, required=True, help="Path to the PDF file")
    parser.add_argument("--return-text", action="store_true", help="Return the extracted text")
    args = parser.parse_args()

    ocr = OCRPlugin()
    text = ocr.process_pdf(args.pdf_path)
    print(text)
