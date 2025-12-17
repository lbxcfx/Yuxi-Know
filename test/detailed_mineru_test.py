#!/usr/bin/env python3
"""
详细的 MinerU API 测试
"""

import requests
import json

def test_mineru_detailed():
    """详细测试 MinerU API"""
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    url = "https://mineru.net/api/v4/extract/task"
    
    # 测试不同的认证方式
    auth_methods = [
        {
            "name": "Bearer Token",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        },
        {
            "name": "Direct Token",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": token
            }
        },
        {
            "name": "API Key Header",
            "headers": {
                "Content-Type": "application/json",
                "X-API-Key": token
            }
        },
        {
            "name": "API Key Header (alternative)",
            "headers": {
                "Content-Type": "application/json",
                "api-key": token
            }
        }
    ]
    
    data = {
        "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
        "is_ocr": True,
        "enable_formula": False,
    }
    
    print("Testing MinerU API with different authentication methods")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Test file: {data['url']}")
    print()
    
    for method in auth_methods:
        print(f"Testing: {method['name']}")
        print(f"Headers: {method['headers']}")
        
        try:
            response = requests.post(url, headers=method['headers'], json=data, timeout=30)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("SUCCESS! Response:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
                return True
            else:
                print(f"Failed: {response.text}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print("-" * 50)
    
    # 测试不同的 API 端点
    print("\nTesting different API endpoints...")
    endpoints = [
        "https://mineru.net/api/v4/extract/task",
        "https://api.mineru.net/v4/extract/task",
        "https://mineru.net/api/v1/extract/task",
        "https://mineru.net/extract/task"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    for endpoint in endpoints:
        print(f"\nTesting endpoint: {endpoint}")
        try:
            response = requests.post(endpoint, headers=headers, json=data, timeout=30)
            print(f"Status Code: {response.status_code}")
            if response.status_code != 404:
                print(f"Response: {response.text[:200]}...")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    return False

def test_with_different_data():
    """测试不同的请求数据格式"""
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    url = "https://mineru.net/api/v4/extract/task"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 测试不同的数据格式
    test_cases = [
        {
            "name": "Original format",
            "data": {
                "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
                "is_ocr": True,
                "enable_formula": False,
            }
        },
        {
            "name": "With additional fields",
            "data": {
                "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
                "is_ocr": True,
                "enable_formula": False,
                "output_format": "text"
            }
        },
        {
            "name": "Minimal format",
            "data": {
                "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf"
            }
        }
    ]
    
    print("\nTesting different data formats...")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Data: {test_case['data']}")
        
        try:
            response = requests.post(url, headers=headers, json=test_case['data'], timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                print("SUCCESS!")
                return True
                
        except Exception as e:
            print(f"Error: {str(e)}")
    
    return False

if __name__ == "__main__":
    print("Starting detailed MinerU API test...")
    
    success1 = test_mineru_detailed()
    success2 = test_with_different_data()
    
    print("\n" + "=" * 70)
    if success1 or success2:
        print("SUCCESS: Found working configuration!")
    else:
        print("FAILED: No working configuration found.")
        print("\nPossible issues:")
        print("1. API Key may be invalid or expired")
        print("2. API endpoint may have changed")
        print("3. Authentication method may be different")
        print("4. Service may be temporarily unavailable")
    print("=" * 70)
