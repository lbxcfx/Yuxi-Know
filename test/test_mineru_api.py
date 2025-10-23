#!/usr/bin/env python3
"""
测试 MinerU API 连接
"""

import os
import sys

import requests
from dotenv import load_dotenv

sys.path.insert(0, ".")

load_dotenv()

def test_mineru_api_connection():
    """测试 MinerU API 连接"""
    api_key = os.getenv("MINERU_API_KEY", "")
    api_url = os.getenv("MINERU_API_URL", "https://mineru.net/api/v4/extract/task")

    print("=" * 60)
    print("测试 MinerU API 连接")
    print("=" * 60)

    if not api_key:
        print("❌ 错误: 未配置 MINERU_API_KEY")
        print("请在 .env 文件中设置 MINERU_API_KEY")
        return False

    print(f"\n✓ API Key: {api_key[:20]}...")
    print(f"✓ API URL: {api_url}")

    # 使用官方示例 PDF 测试
    test_pdf_url = "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    data = {
        "url": test_pdf_url,
        "is_ocr": True,
        "enable_formula": False,
    }

    print(f"\n正在测试 API 调用...")
    print(f"测试文件: {test_pdf_url}")

    try:
        response = requests.post(api_url, headers=headers, json=data, timeout=60)

        print(f"\nHTTP 状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✓ API 调用成功")
            print(f"\n响应内容:")
            print(f"  - code: {result.get('code')}")
            print(f"  - message: {result.get('message')}")
            print(f"  - data: {result.get('data', '')[:100]}...")

            if result.get("code") == 200:
                data_url = result.get("data", "")
                if data_url:
                    print(f"\n尝试下载结果...")
                    result_response = requests.get(data_url, timeout=30)
                    if result_response.status_code == 200:
                        text = result_response.text
                        print(f"✓ 结果下载成功")
                        print(f"✓ 提取文本长度: {len(text)} 字符")
                        print(f"\n文本预览 (前 200 个字符):")
                        print("-" * 60)
                        print(text[:200])
                        print("-" * 60)
                        return True
                    else:
                        print(f"❌ 结果下载失败: HTTP {result_response.status_code}")
                        return False
                else:
                    print(f"❌ API 未返回数据 URL")
                    return False
            else:
                print(f"❌ API 返回错误: {result.get('message')}")
                return False
        else:
            print(f"❌ API 调用失败")
            print(f"响应内容: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_mineru_api_connection()

    print("\n" + "=" * 60)
    if success:
        print("✓ MinerU API 测试成功！")
        print("你现在可以在知识库中使用 MinerU OCR 功能了")
    else:
        print("✗ MinerU API 测试失败")
        print("\n请检查:")
        print("1. MINERU_API_KEY 是否正确")
        print("2. API Key 是否过期")
        print("3. 网络连接是否正常")
    print("=" * 60)

    sys.exit(0 if success else 1)
