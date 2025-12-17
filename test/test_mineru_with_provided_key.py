#!/usr/bin/env python3
"""
使用提供的 API Key 测试 MinerU API
"""

import requests
import json
import time
import sys
import os

# 设置控制台编码以支持中文显示
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def test_mineru_api():
    """测试 MinerU API 功能"""
    
    # 你提供的 API key
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    url = "https://mineru.net/api/v4/extract/task"
    header = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
        "is_ocr": True,
        "enable_formula": False,
    }

    print("=" * 80)
    print("MinerU API 测试程序")
    print("=" * 80)
    print(f"API URL: {url}")
    print(f"测试文件: {data['url']}")
    print(f"OCR 启用: {data['is_ocr']}")
    print(f"公式识别: {data['enable_formula']}")
    print()

    try:
        print("正在发送请求到 MinerU API...")
        res = requests.post(url, headers=header, json=data, timeout=60)
        
        print(f"HTTP 状态码: {res.status_code}")
        print()
        
        if res.status_code == 200:
            response_data = res.json()
            print("API 响应:")
            print(json.dumps(response_data, indent=2, ensure_ascii=False))
            print()
            
            # 检查响应结构
            if "data" in response_data:
                data_url = response_data["data"]
                print(f"提取结果 URL: {data_url}")
                print()
                
                # 尝试下载提取结果
                print("正在下载提取结果...")
                try:
                    result_res = requests.get(data_url, timeout=30)
                    if result_res.status_code == 200:
                        extracted_text = result_res.text
                        print("[SUCCESS] 成功下载提取结果")
                        print(f"[SUCCESS] 提取文本长度: {len(extracted_text)} 字符")
                        print()
                        print("提取的文本内容:")
                        print("-" * 80)
                        print(extracted_text)
                        print("-" * 80)
                        return True
                    else:
                        print(f"[ERROR] 下载结果失败: HTTP {result_res.status_code}")
                        print(f"错误信息: {result_res.text}")
                        return False
                except Exception as e:
                    print(f"[ERROR] 下载结果时出错: {str(e)}")
                    return False
            else:
                print("[ERROR] API 响应中没有 'data' 字段")
                return False
        else:
            print(f"[ERROR] API 请求失败")
            print(f"错误响应: {res.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("[ERROR] 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] 连接错误")
        return False
    except Exception as e:
        print(f"[ERROR] 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_different_options():
    """测试不同的配置选项"""
    print("\n" + "=" * 80)
    print("测试不同配置选项")
    print("=" * 80)
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    url = "https://mineru.net/api/v4/extract/task"
    header = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 测试配置1: 启用公式识别
    print("\n测试配置1: 启用公式识别")
    data1 = {
        "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
        "is_ocr": True,
        "enable_formula": True,
    }
    
    try:
        res1 = requests.post(url, headers=header, json=data1, timeout=60)
        print(f"状态码: {res1.status_code}")
        if res1.status_code == 200:
            result1 = res1.json()
            print(f"响应: {result1}")
        else:
            print(f"错误: {res1.text}")
    except Exception as e:
        print(f"错误: {str(e)}")
    
    # 测试配置2: 禁用 OCR
    print("\n测试配置2: 禁用 OCR")
    data2 = {
        "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
        "is_ocr": False,
        "enable_formula": False,
    }
    
    try:
        res2 = requests.post(url, headers=header, json=data2, timeout=60)
        print(f"状态码: {res2.status_code}")
        if res2.status_code == 200:
            result2 = res2.json()
            print(f"响应: {result2}")
        else:
            print(f"错误: {res2.text}")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    print("开始测试 MinerU API...")
    
    # 主要测试
    success = test_mineru_api()
    
    # 额外测试
    test_different_options()
    
    print("\n" + "=" * 80)
    if success:
        print("[SUCCESS] MinerU API 测试成功！")
        print("API Key 有效，可以正常使用 MinerU 服务")
    else:
        print("[FAILED] MinerU API 测试失败")
        print("请检查 API Key 是否有效或网络连接是否正常")
    print("=" * 80)
