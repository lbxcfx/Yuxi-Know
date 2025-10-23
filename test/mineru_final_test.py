#!/usr/bin/env python3
"""
MinerU API 最终测试和诊断
"""

import requests
import json
from datetime import datetime

def main():
    """主测试函数"""
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    print("MinerU API 测试结果总结")
    print("=" * 80)
    
    # 1. Token 状态检查
    print("1. Token 状态检查:")
    print("-" * 40)
    exp_timestamp = 1762085083
    exp_date = datetime.fromtimestamp(exp_timestamp)
    current_date = datetime.now()
    
    print(f"   Token 长度: {len(token)} 字符")
    print(f"   过期时间: {exp_date}")
    print(f"   当前时间: {current_date}")
    print(f"   Token 有效: {'是' if current_date < exp_date else '否'}")
    print(f"   剩余天数: {(exp_date - current_date).days} 天")
    print(f"   角色权限: ROLE_REGISTER (注册用户)")
    print(f"   发行方: OpenXLab")
    print()
    
    # 2. API 测试
    print("2. API 调用测试:")
    print("-" * 40)
    
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
        print(f"   HTTP 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("   [SUCCESS] API 调用成功!")
            print(f"   响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return True
        else:
            error_data = response.json()
            print(f"   [FAILED] API 调用失败")
            print(f"   错误代码: {error_data.get('msgCode', 'N/A')}")
            print(f"   错误信息: {error_data.get('msg', 'N/A')}")
            print(f"   跟踪ID: {error_data.get('traceId', 'N/A')}")
            
    except Exception as e:
        print(f"   [ERROR] 请求异常: {str(e)}")
    
    print()
    
    # 3. 问题诊断
    print("3. 问题诊断:")
    print("-" * 40)
    print("   根据测试结果，问题可能包括:")
    print("   • Token 角色权限不足 (ROLE_REGISTER)")
    print("   • 需要激活 API 访问权限")
    print("   • 账户可能需要升级或验证")
    print("   • API 服务可能有使用限制")
    print()
    
    # 4. 建议解决方案
    print("4. 建议解决方案:")
    print("-" * 40)
    print("   1. 检查 MinerU 账户状态:")
    print("      - 登录 MinerU 官网检查账户状态")
    print("      - 确认是否需要激活 API 访问权限")
    print("      - 检查是否有使用限制或配额")
    print()
    print("   2. 联系 MinerU 技术支持:")
    print("      - 提供你的 Client ID: lkzdx57nvy22jkpq9x2w")
    print("      - 提供你的 UUID: 232de259-2382-4d54-9f0b-655cb2d1a650")
    print("      - 说明需要 API 访问权限")
    print()
    print("   3. 尝试重新获取 API Key:")
    print("      - 在 MinerU 控制台重新生成 API Key")
    print("      - 确保选择正确的权限级别")
    print()
    print("   4. 检查 API 文档:")
    print("      - 查看最新的 API 文档")
    print("      - 确认认证方式和端点是否有变化")
    print()
    
    # 5. 测试代码
    print("5. 你的测试代码:")
    print("-" * 40)
    print("   你的代码本身是正确的:")
    print("   ```python")
    print("   import requests")
    print("   ")
    print("   token = \"你的API token\"")
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
    
    print("=" * 80)
    if success:
        print("[SUCCESS] MinerU API 测试通过!")
    else:
        print("[INFO] 测试完成，请根据上述建议解决问题")
    print("=" * 80)
