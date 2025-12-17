#!/usr/bin/env python3
"""
MinerU API 测试总结报告
"""

import requests
import json
from datetime import datetime

def main():
    """主测试函数"""
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    print("MinerU API Test Summary")
    print("=" * 60)
    
    # 1. Token Status
    print("1. Token Status:")
    print("-" * 30)
    exp_timestamp = 1762085083
    exp_date = datetime.fromtimestamp(exp_timestamp)
    current_date = datetime.now()
    
    print(f"   Token Length: {len(token)} chars")
    print(f"   Expires: {exp_date}")
    print(f"   Current: {current_date}")
    print(f"   Valid: {'Yes' if current_date < exp_date else 'No'}")
    print(f"   Days Left: {(exp_date - current_date).days}")
    print(f"   Role: ROLE_REGISTER")
    print(f"   Issuer: OpenXLab")
    print()
    
    # 2. API Test
    print("2. API Test:")
    print("-" * 30)
    
    url = "https://mineru.net/api/v4/extract/task"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "url": "https://cdn-mineru.openxlab.org.cn/demo/example.pdf",
        "is_ocr": True,
        "enable_formula": False,
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   [SUCCESS] API call successful!")
            print(f"   Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            error_data = response.json()
            print(f"   [FAILED] API call failed")
            print(f"   Error Code: {error_data.get('msgCode', 'N/A')}")
            print(f"   Error Message: {error_data.get('msg', 'N/A')}")
            print(f"   Trace ID: {error_data.get('traceId', 'N/A')}")
            
    except Exception as e:
        print(f"   [ERROR] Request exception: {str(e)}")
    
    print()
    
    # 3. Problem Analysis
    print("3. Problem Analysis:")
    print("-" * 30)
    print("   Based on test results, possible issues:")
    print("   - Token role insufficient (ROLE_REGISTER)")
    print("   - API access permission not activated")
    print("   - Account may need upgrade or verification")
    print("   - API service may have usage restrictions")
    print()
    
    # 4. Solutions
    print("4. Recommended Solutions:")
    print("-" * 30)
    print("   1. Check MinerU account status:")
    print("      - Login to MinerU website")
    print("      - Verify API access permissions")
    print("      - Check usage limits or quotas")
    print()
    print("   2. Contact MinerU support:")
    print("      - Provide Client ID: lkzdx57nvy22jkpq9x2w")
    print("      - Provide UUID: 232de259-2382-4d54-9f0b-655cb2d1a650")
    print("      - Request API access permissions")
    print()
    print("   3. Try getting new API Key:")
    print("      - Regenerate API Key in MinerU console")
    print("      - Ensure correct permission level")
    print()
    
    # 5. Your Code
    print("5. Your Test Code:")
    print("-" * 30)
    print("   Your code is correct:")
    print("   ```python")
    print("   import requests")
    print("   ")
    print("   token = \"your_api_token\"")
    print("   url = \"https://mineru.net/api/v4/extract/task\"")
    print("   header = {")
    print("       \"Content-Type\": \"application/json\",")
    print("       \"Authorization\": f\"Bearer {token}\"")
    print("   }")
    print("   data = {")
    print("       \"url\": \"https://cdn-mineru.openxlab.org.cn/demo/example.pdf\",")
    print("       \"is_ocr\": True,")
    print("       \"enable_formula\": False,")
    print("   }")
    print("   ")
    print("   res = requests.post(url, headers=header, json=data)")
    print("   print(res.status_code)")
    print("   print(res.json())")
    print("   ```")
    print()
    
    return False

if __name__ == "__main__":
    success = main()
    
    print("=" * 60)
    if success:
        print("[SUCCESS] MinerU API test passed!")
    else:
        print("[INFO] Test completed. Please follow the recommendations above.")
    print("=" * 60)
