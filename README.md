# 版本管理服务

一个基于 Flask 的版本管理服务，提供版本比较、安装包上传和下载功能，支持开发和生产环境部署。

## 功能特性

- ✅ 版本比较接口 - 比较传入版本号与本地最新版本
- ✅ 安装包上传接口 - 上传最新的安装包文件
- ✅ 安装包下载接口 - 下载本地存储的最新安装包
- ✅ 文件存储版本号 - 使用文本文件存储最新版本信息
- ✅ 接口安全认证 - HMAC-SHA256签名验证
- ✅ 完整日志系统 - 操作记录和错误追踪
- ✅ 生产环境支持 - 支持Waitress WSGI服务器
- ✅ Docker容器化 - 支持容器化部署

## 安装依赖

```bash
pip install -r requirements.txt
```

## 快速开始

### 开发环境

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动开发服务
python app.py
# 或使用启动脚本
./start_server.sh

# 3. 访问服务
# 服务地址: http://localhost:10250
# Web界面: http://localhost:10250
```

### 生产环境

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动生产服务
export FLASK_ENV=production
python app.py
# 或使用生产环境脚本
./start_production.sh
```

## 文件结构

```
version-control/
├── app.py                 # 主程序文件
├── wsgi.py               # WSGI入口文件（生产环境）
├── requirements.txt       # 依赖文件
├── start_server.sh        # 开发环境启动脚本
├── start_production.sh    # 生产环境启动脚本
├── test_auth.py          # 接口测试工具
├── latest_version.txt    # 版本号存储文件
├── logs/                 # 日志文件目录
│   └── version_control.log
├── packages/             # 安装包存储目录
│   └── latest_package.exe
├── README.md             # 项目说明
└── version_control.md    # 详细接口文档
```

## 环境配置

### 开发环境
- **服务器**: Flask开发服务器
- **调试模式**: 开启
- **端口**: 10250
- **日志级别**: INFO

### 生产环境
- **服务器**: Waitress WSGI服务器
- **调试模式**: 关闭
- **线程数**: 4
- **端口**: 10250
- **日志级别**: INFO

## 详细文档

- [接口文档](version_control.md) - 完整的API接口说明
- [部署指南](version_control.md#部署说明) - 生产环境部署说明
- [安全认证](version_control.md#接口认证) - 接口安全认证机制