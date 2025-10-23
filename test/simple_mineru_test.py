#!/usr/bin/env python3
"""
简单的 MinerU API 测试程序
"""

import requests
import json

def test_mineru_simple():
    """简单测试 MinerU API"""
    
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

    print("Testing MinerU API...")
    print(f"URL: {url}")
    print(f"Test file: {data['url']}")
    print()

    try:
        res = requests.post(url, headers=header, json=data, timeout=60)
        print(f"Status Code: {res.status_code}")
        
        if res.status_code == 200:
            result = res.json()
            print("Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if "data" in result:
                data_url = result["data"]
                print(f"\nResult URL: {data_url}")
                
                # 尝试下载结果
                print("\nDownloading result...")
                result_res = requests.get(data_url, timeout=30)
                if result_res.status_code == 200:
                    text = result_res.text
                    print(f"Success! Extracted text length: {len(text)} characters")
                    print("\nExtracted text preview (first 300 chars):")
                    print("-" * 60)
                    print(text[:300])
                    print("-" * 60)
                    return True
                else:
                    print(f"Failed to download result: HTTP {result_res.status_code}")
                    return False
            else:
                print("No data URL in response")
                return False
        else:
            print(f"API request failed")
            print(f"Response: {res.text}")
            return False
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_mineru_simple()
    
    print("\n" + "=" * 60)
    if success:
        print("SUCCESS: MinerU API test passed!")
        print("Your API key is working correctly.")
    else:
        print("FAILED: MinerU API test failed.")
        print("Please check your API key or network connection.")
    print("=" * 60)
