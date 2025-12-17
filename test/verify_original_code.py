#!/usr/bin/env python3
"""
验证原始代码并添加调试信息
"""

import requests
import json

def test_original_code():
    """测试你提供的原始代码"""
    
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

    print("Testing with your original code...")
    print("=" * 60)
    print(f"Token (first 50 chars): {token[:50]}...")
    print(f"URL: {url}")
    print(f"Headers: {header}")
    print(f"Data: {data}")
    print()

    try:
        print("Sending request...")
        res = requests.post(url, headers=header, json=data, timeout=60)
        
        print(f"Status Code: {res.status_code}")
        print(f"Response Headers: {dict(res.headers)}")
        print()
        
        if res.status_code == 200:
            result = res.json()
            print("SUCCESS! Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            if "data" in result:
                print(f"\nData URL: {result['data']}")
                return True
        else:
            print("FAILED! Response:")
            print(res.text)
            
            # 尝试解析错误响应
            try:
                error_data = res.json()
                print("\nParsed error response:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                print("Could not parse error response as JSON")
                
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return False

def check_token_details():
    """检查 token 的详细信息"""
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    print("\nToken Analysis:")
    print("=" * 60)
    
    # 手动解析 JWT payload（从之前的分析我们知道 exp: 1762085083）
    from datetime import datetime
    
    exp_timestamp = 1762085083
    exp_date = datetime.fromtimestamp(exp_timestamp)
    current_date = datetime.now()
    
    print(f"Token length: {len(token)} characters")
    print(f"Expiration timestamp: {exp_timestamp}")
    print(f"Expiration date: {exp_date}")
    print(f"Current date: {current_date}")
    print(f"Token valid: {current_date < exp_date}")
    print(f"Days until expiration: {(exp_date - current_date).days}")
    
    # 从 token 中提取的信息
    print(f"\nToken info (from previous analysis):")
    print(f"Role: ROLE_REGISTER")
    print(f"Issuer: OpenXLab")
    print(f"Client ID: lkzdx57nvy22jkpq9x2w")
    print(f"UUID: 232de259-2382-4d54-9f0b-655cb2d1a650")

def test_alternative_approaches():
    """测试其他可能的方法"""
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    print("\nTesting alternative approaches...")
    print("=" * 60)
    
    # 测试是否需要先登录或获取新的 token
    login_url = "https://mineru.net/api/v4/auth/login"
    
    # 尝试不同的请求方式
    test_cases = [
        {
            "name": "GET request to check API status",
            "method": "GET",
            "url": "https://mineru.net/api/v4/status",
            "headers": {"Authorization": f"Bearer {token}"},
            "data": None
        },
        {
            "name": "POST with form data",
            "method": "POST", 
            "url": "https://mineru.net/api/v4/extract/task",
            "headers": {"Authorization": f"Bearer {token}"},
            "data": {
                "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
                "is_ocr": "true",
                "enable_formula": "false"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{test_case['name']}:")
        try:
            if test_case['method'] == 'GET':
                response = requests.get(test_case['url'], headers=test_case['headers'], timeout=30)
            else:
                response = requests.post(test_case['url'], headers=test_case['headers'], 
                                       json=test_case['data'], timeout=30)
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("MinerU API Verification Test")
    print("=" * 80)
    
    # 检查 token 详情
    check_token_details()
    
    # 测试原始代码
    success = test_original_code()
    
    # 测试其他方法
    test_alternative_approaches()
    
    print("\n" + "=" * 80)
    if success:
        print("SUCCESS: Your API key is working!")
    else:
        print("FAILED: API key authentication failed.")
        print("\nPossible solutions:")
        print("1. Check if you need to activate your account or upgrade permissions")
        print("2. Verify the API key is correct and has the right permissions")
        print("3. Contact MinerU support for assistance")
        print("4. Check if there are any usage limits or restrictions")
    print("=" * 80)
