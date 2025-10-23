#!/usr/bin/env python3
"""
简单的 JWT Token 检查
"""

import base64
import json

def simple_jwt_decode():
    """简单解码 JWT token"""
    
    token = "eyJ0eXBlIjoiSldUIiwiYWxnIjoiSFM1MTIifQ.eyJqdGkiOiIzODkwMDE4MiIsInJvbCI6IlJPTEVfUkVHSVNURSIiLCJpc3MiOiJPcGVuWExhYiIsImlhdCI6MTc2MDg3NTQ4MywiY2xpZW50SWQiOiJsa3pkeDU3bnZ5MjJqa3BxOXgydyIsInBob25lIjoiIiwib3BlbklkIjpudWxsLCJ1dWlkIjoiMjMyZGUyNTktMjM4Mi00ZDU0LTlmMGItNjU1Y2IyZDFhNjUwIiwiZW1haWwiOiIiLCJleHAiOjE3NjIwODUwODN9.ZnTZHC8XMwKYwsUAYLl13NapVEVriux1U1a5jLpN6vD6wevIHug8yU5xWjtZioPnD28AO5_vx5GfiXce5iFrEw"
    
    print("JWT Token Analysis")
    print("=" * 50)
    
    # 分割 token
    parts = token.split('.')
    print(f"Token parts: {len(parts)}")
    
    if len(parts) >= 2:
        # 解码 header
        print("\nHeader:")
        try:
            header_padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
            header_decoded = base64.urlsafe_b64decode(header_padded)
            header_json = json.loads(header_decoded)
            print(json.dumps(header_json, indent=2))
        except Exception as e:
            print(f"Header decode error: {e}")
        
        # 解码 payload
        print("\nPayload:")
        try:
            payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload_decoded = base64.urlsafe_b64decode(payload_padded)
            payload_json = json.loads(payload_decoded)
            print(json.dumps(payload_json, indent=2))
            
            # 检查过期时间
            if 'exp' in payload_json:
                exp_timestamp = payload_json['exp']
                from datetime import datetime
                exp_date = datetime.fromtimestamp(exp_timestamp)
                current_date = datetime.now()
                
                print(f"\nExpiration: {exp_date}")
                print(f"Current: {current_date}")
                
                if current_date > exp_date:
                    print("❌ TOKEN IS EXPIRED!")
                else:
                    print("✅ Token is valid")
                    
        except Exception as e:
            print(f"Payload decode error: {e}")
    
    # 手动检查过期时间（从 token 中可以看到 exp: 1762085083）
    print("\nManual check:")
    exp_timestamp = 1762085083
    from datetime import datetime
    exp_date = datetime.fromtimestamp(exp_timestamp)
    current_date = datetime.now()
    
    print(f"Expiration timestamp: {exp_timestamp}")
    print(f"Expiration date: {exp_date}")
    print(f"Current date: {current_date}")
    
    if current_date > exp_date:
        print("❌ TOKEN IS EXPIRED!")
        print(f"Expired {(current_date - exp_date).days} days ago")
    else:
        print("✅ Token is still valid")

if __name__ == "__main__":
    simple_jwt_decode()
