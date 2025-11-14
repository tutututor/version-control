# 版本管理服务接口文档

## 概述

版本管理服务提供三个核心接口：版本比较、安装包上传和安装包下载。服务使用文件存储版本信息和安装包，支持语义化版本号比较。

## 基础信息

- **服务地址**: http://192.168.210.241:10250
- **默认端口**: 10250
- **版本格式**: x.y.z (如 1.0.3)
- **存储方式**: 文件存储

## 接口列表

### 1. 版本比较接口

**接口路径**: `GET /api/version/compare`

**功能描述**: 比较传入版本号与本地最新版本号，根据比较结果返回不同的状态码和消息。

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 | 示例 |
|--------|------|------|------|------|
| version | string | 是 | 需要比较的版本号 | 1.0.3 |

**响应格式**:

```json
{
    "code": 0,                    // 状态码
    "message": "描述信息",        // 消息描述
    "input_version": "1.0.3",    // 传入的版本号
    "latest_version": "1.0.3",   // 本地最新版本号
    "updated": true              // 可选：是否更新了本地版本
}
```

**状态码说明**:

| 状态码 | 含义 | 描述 |
|--------|------|------|
| 0 | 版本相同或已更新 | 传入版本与本地版本相同，或本地版本已更新为传入版本 |
| 1 | 本地版本更高 | 本地版本比传入版本高，需要更新客户端 |

**响应示例**:

**情况1：版本相同**
```json
{
    "code": 0,
    "message": "当前版本是最新版本",
    "input_version": "1.0.3",
    "latest_version": "1.0.3"
}
```

**情况2：本地版本较低（自动更新）**
```json
{
    "code": 0,
    "message": "当前版本是最新版本",
    "input_version": "1.0.3",
    "latest_version": "1.0.3",
    "updated": true
}
```

**情况3：本地版本较高**
```json
{
    "code": 1,
    "message": "当前最新版本是1.2.0，请更新最新版本",
    "input_version": "1.0.0",
    "latest_version": "1.2.0"
}
```

**错误响应**:

```json
{
    "error": "错误描述"
}
```

### 2. 安装包上传接口

**接口路径**: `POST /api/upload/package`

**功能描述**: 上传最新的安装包文件，替换本地存储的旧安装包。

**请求格式**: `multipart/form-data`

**请求参数**:

| 参数名 | 类型 | 必需 | 描述 |
|--------|------|------|------|
| file | file | 是 | 安装包文件 |

**成功响应**:

```json
{
    "status": "success",
    "message": "安装包上传成功",
    "file_size": 1024000,
    "file_path": "packages/latest_package.exe"
}
```

**错误响应**:

```json
{
    "error": "错误描述"
}
```

### 3. 安装包下载接口

**接口路径**: `GET /api/download/latest`

**功能描述**: 下载本地存储的最新安装包文件。

**响应**: 返回文件流，下载文件名为 `DwtAI-Hub-Install-X64.exe`

**成功响应**: 直接返回文件流

**错误响应**:

```json
{
    "error": "本地安装包不存在，请先上传安装包",
    "upload_endpoint": "/api/upload/package"
}
```

### cURL 示例

```bash
# 版本比较
curl "http://192.168.210.241:10250/api/version/compare?version=1.0.3"

# 上传安装包
curl -X POST -F "file=@my_package.exe" http://192.168.210.241:10250/api/upload/package

# 下载安装包
curl -O http://192.168.210.241:10250/api/download/latest
```

## 版本比较逻辑

### 语义化版本比较

版本号采用 `x.y.z` 格式，比较规则：

1. **逐位比较**: 从左到右依次比较主版本号、次版本号、修订号
2. **自动补齐**: 较短的版本号用0补齐（如 1.0 视为 1.0.0）
3. **比较结果**:
   - `-1`: 版本1 < 版本2
   - `0`: 版本1 = 版本2  
   - `1`: 版本1 > 版本2

### 业务逻辑

1. **版本相同** (`code=0`): 传入版本与本地版本相同
2. **本地版本较低** (`code=0`): 自动更新本地版本为传入版本
3. **本地版本较高** (`code=1`): 提示客户端需要更新

## 文件存储

### 版本文件
- **路径**: `latest_version.txt`
- **格式**: 纯文本，单行版本号
- **初始版本**: 1.0.3

### 安装包文件
- **路径**: `packages/latest_package.exe`
- **特点**: 只保留最新版本，上传新包时自动删除旧包

## 错误处理

### 常见错误

1. **缺少参数**: 返回 400 状态码
2. **版本格式错误**: 返回 400 状态码
3. **文件不存在**: 返回 404 状态码
4. **服务器错误**: 返回 500 状态码

### 错误响应格式

```json
{
    "error": "错误描述信息"
}
```

## 接口认证

### 安全机制

所有接口都使用HMAC-SHA256签名进行认证，防止未授权访问。

### 认证流程

1. **生成时间戳**: 获取当前时间戳（秒）
2. **构建签名数据**: `{method}:{path}:{timestamp}:{query_string}`
3. **计算HMAC签名**: 使用密钥对签名数据进行HMAC-SHA256计算
4. **添加请求头**: 在请求头中包含时间戳和签名

### 请求头要求

| 请求头 | 说明 | 示例 |
|--------|------|------|
| X-Timestamp | 当前时间戳（秒） | 1763101680 |
| X-Signature | HMAC-SHA256签名 | de2748097e9d810c232644b9504744e757c5805cf30b1de8ee3a3614f2f4a22e |

### 认证密钥

默认密钥：`version_control_secret_key_2025`

**生产环境建议**: 通过环境变量设置密钥
```bash
export SECRET_KEY="your_production_secret_key"
```

### 认证示例

```python
import time
import hmac
import hashlib

# 认证信息
SECRET_KEY = "version_control_secret_key_2024"
method = "GET"
path = "/api/version/compare"
timestamp = str(int(time.time()))
query_string = "version=1.0.3"

# 生成签名
sign_data = f"{method}:{path}:{timestamp}:{query_string}"
signature = hmac.new(
    SECRET_KEY.encode('utf-8'),
    sign_data.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# 设置请求头
headers = {
    'X-Timestamp': timestamp,
    'X-Signature': signature
}
```

### 服务配置

| 环境 | 服务器 | 端口 | 调试模式 | 线程数 |
|------|--------|------|----------|--------|
| 开发 | Flask开发服务器 | 10250 | 开启 | 单线程 |
| 生产 | Waitress WSGI服务器 | 10250 | 关闭 | 4线程 |
