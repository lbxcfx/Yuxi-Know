#!/usr/bin/env python3
"""
检查 JWT Token 的有效性
"""

import base64
import json
from datetime import datetime

def decode_jwt_payload(token):
    """解码 JWT token 的 payload 部分"""
    try:
        # JWT token 由三部分组成，用 . 分隔
        parts = token.split('.')
        if len(parts) != 3:
            return None, "Invalid JWT format"
        
        # 第二部分是 payload
        payload = parts[1]
        
        # 添加必要的 padding
        missing_padding = len(payload) % 4
        if missing_padding:
            payload += '=' * (4 - missing_padding)
        
        # Base64 解码
        try:
            decoded_bytes = base64.urlsafe_b64decode(payload)
            decoded_str = decoded_bytes.decode('utf-8')
        except Exception as e:
            # 如果 urlsafe 解码失败，尝试标准 base64 解码
            try:
                decoded_bytes = base64.b64decode(payload)
                decoded_str = decoded_bytes.decode('utf-8')
            except Exception as e2:
                return None, f"Base64 decode failed: {e}, {e2}"
        
        # 解析 JSON
        payload_data = json.loads(decoded_str)
        return payload_data, None
        
    except Exception as e:
        return None, str(e)

def check_token_validity():
    """检查 token 的有效性"""
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    print("JWT Token Analysis")
    print("=" * 60)
    
    # 解码 token
    payload, error = decode_jwt_payload(token)
    if error:
        print(f"Error decoding token: {error}")
        return
    
    print("Token Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()
    
    # 检查过期时间
    if 'exp' in payload:
        exp_timestamp = payload['exp']
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        current_datetime = datetime.now()
        
        print(f"Issued at (iat): {datetime.fromtimestamp(payload.get('iat', 0))}")
        print(f"Expires at (exp): {exp_datetime}")
        print(f"Current time: {current_datetime}")
        print()
        
        if current_datetime > exp_datetime:
            print("❌ TOKEN EXPIRED!")
            print(f"Token expired {(current_datetime - exp_datetime).days} days ago")
        else:
            print("✅ Token is still valid")
            print(f"Token expires in {(exp_datetime - current_datetime).days} days")
    else:
        print("No expiration time found in token")
    
    # 检查其他重要字段
    print("\nToken Details:")
    print(f"Role: {payload.get('rol', 'N/A')}")
    print(f"Issuer: {payload.get('iss', 'N/A')}")
    print(f"Client ID: {payload.get('clientId', 'N/A')}")
    print(f"UUID: {payload.get('uuid', 'N/A')}")

if __name__ == "__main__":
    check_token_validity()
