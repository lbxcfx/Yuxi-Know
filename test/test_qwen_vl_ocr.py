"""
测试 Qwen-VL OCR 功能
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.plugins import ocr

def test_qwen_vl_image():
    """测试 Qwen-VL 处理图片"""
    print("=" * 60)
    print("测试 Qwen-VL OCR 处理图片")
    print("=" * 60)

    # 检查 API key
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        print("❌ 未配置 DASHSCOPE_API_KEY")
        return False

    print(f"✅ DASHSCOPE_API_KEY 已配置: {api_key[:10]}...")

    # 创建测试图片
    test_image_path = "/app/test/data/test.jpeg"
    if not os.path.exists(test_image_path):
        print(f"⚠️ 测试图片不存在，创建测试图片...")
        from PIL import Image, ImageDraw

        # 创建目录
        os.makedirs(os.path.dirname(test_image_path), exist_ok=True)

        # 创建图片
        img = Image.new('RGB', (800, 400), color='white')
        draw = ImageDraw.Draw(img)

        # 添加文字
        text = "测试文字 OCR\nTest Text Recognition\n123456789"
        draw.text((50, 100), text, fill='black')

        # 保存
        img.save(test_image_path)
        print(f"✅ 测试图片已创建: {test_image_path}")
    else:
        print(f"✅ 使用现有测试图片: {test_image_path}")

    try:
        print("\n开始处理图片...")
        result_text = ocr.process_file_qwen_vl(test_image_path)

        print("\n" + "=" * 60)
        print("OCR 识别结果:")
        print("=" * 60)
        print(result_text)
        print("=" * 60)
        print(f"\n✅ OCR 处理成功，识别文字长度: {len(result_text)} 字符")

        return True

    except Exception as e:
        print(f"\n❌ OCR 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_qwen_vl_image()
    sys.exit(0 if success else 1)
