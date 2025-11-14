#!/usr/bin/env python3
"""
版本管理服务接口加密测试工具
用于生成正确的请求签名来测试接口
"""

import hashlib
import hmac
import time
import requests

# 加密密钥（与app.py中的SECRET_KEY保持一致）
SECRET_KEY = "version_control_secret_key_2024"

def generate_signature(method, path, timestamp, query_string=""):
    """生成接口签名"""
    sign_data = f"{method}:{path}:{timestamp}:{query_string}"
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        sign_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def test_version_compare():
    """测试版本比较接口"""
    base_url = "http://localhost:10250"
    path = "/api/version/compare"
    method = "GET"
    
    # 生成时间戳和签名
    timestamp = str(int(time.time()))
    query_string = "version=1.0.3"
    signature = generate_signature(method, path, timestamp, query_string)
    
    # 设置请求头
    headers = {
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }
    
    # 发送请求
    url = f"{base_url}{path}?{query_string}"
    response = requests.get(url, headers=headers)
    
    print("=== 版本比较接口测试 ===")
    print(f"请求URL: {url}")
    print(f"时间戳: {timestamp}")
    print(f"签名: {signature}")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    print()

def test_download_latest():
    """测试下载接口"""
    base_url = "http://localhost:10250"
    path = "/api/download/latest"
    method = "GET"
    
    # 生成时间戳和签名
    timestamp = str(int(time.time()))
    signature = generate_signature(method, path, timestamp)
    
    # 设置请求头
    headers = {
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }
    
    # 发送请求
    url = f"{base_url}{path}"
    response = requests.get(url, headers=headers)
    
    print("=== 下载接口测试 ===")
    print(f"请求URL: {url}")
    print(f"时间戳: {timestamp}")
    print(f"签名: {signature}")
    print(f"响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        # 保存下载的文件
        with open('downloaded_package.exe', 'wb') as f:
            f.write(response.content)
        print("文件下载成功: downloaded_package.exe")
    else:
        print(f"响应内容: {response.text}")
    print()

def test_upload_package():
    """测试上传接口"""
    base_url = "http://localhost:10250"
    path = "/api/upload/package"
    method = "POST"
    
    # 生成时间戳和签名
    timestamp = str(int(time.time()))
    signature = generate_signature(method, path, timestamp)
    
    # 设置请求头
    headers = {
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }
    
    # 准备文件
    files = {'file': ('test_package.exe', open('test_package.exe', 'rb'), 'application/octet-stream')}
    
    # 发送请求
    url = f"{base_url}{path}"
    response = requests.post(url, headers=headers, files=files)
    
    print("=== 上传接口测试 ===")
    print(f"请求URL: {url}")
    print(f"时间戳: {timestamp}")
    print(f"签名: {signature}")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    print()

def generate_auth_headers(method, path, query_string=""):
    """生成认证头信息"""
    timestamp = str(int(time.time()))
    signature = generate_signature(method, path, timestamp, query_string)
    
    return {
        'X-Timestamp': timestamp,
        'X-Signature': signature
    }

def print_auth_info():
    """打印认证信息"""
    print("=== 接口认证信息 ===")
    print(f"密钥: {SECRET_KEY}")
    print("签名算法: HMAC-SHA256")
    print("签名数据格式: {method}:{path}:{timestamp}:{query_string}")
    print("请求头要求:")
    print("  X-Timestamp: 当前时间戳（秒）")
    print("  X-Signature: HMAC-SHA256签名")
    print()

if __name__ == "__main__":
    print_auth_info()
    
    # 测试版本比较接口
    test_version_compare()
    
    # 测试下载接口
    test_download_latest()
    
    # 测试上传接口（需要先有test_package.exe文件）
    # test_upload_package()
    
    print("测试完成！")