#!/bin/bash

# 版本管理服务统一启动脚本
# 支持开发环境和生产环境

# 配置变量
SERVICE_NAME="version-control-service"
IMAGE_NAME="version-control-service:latest"

# 默认环境（支持 dev 或 production）
ENVIRONMENT="${1:-dev}"

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "错误：Docker未安装或未启动"
    exit 1
fi

# 动态获取当前目录
CURRENT_DIR=$(pwd)

# 创建必要目录并设置权限
mkdir -p $CURRENT_DIR/logs
mkdir -p $CURRENT_DIR/packages
chmod -R 755 $CURRENT_DIR/logs
chmod -R 755 $CURRENT_DIR/packages

# 验证环境参数
if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo "错误：环境参数必须是 'dev' 或 'production'"
    echo "用法: $0 [dev|production]"
    exit 1
fi

echo "========================================"
echo "版本管理服务启动"
echo "========================================"
echo "挂载目录: $CURRENT_DIR"
echo "服务名称: $SERVICE_NAME"
echo "环境: $ENVIRONMENT"
echo ""

# 检查必要文件
if [ ! -f "app.py" ]; then
    echo "错误：app.py 文件不存在"
    exit 1
fi

if [ ! -f "pyproject.toml" ]; then
    echo "错误：pyproject.toml 文件不存在"
    exit 1
fi

# 停止并删除旧容器
echo "停止旧容器..."
docker stop $SERVICE_NAME 2>/dev/null || true
docker rm $SERVICE_NAME 2>/dev/null || true

echo "启动Docker容器..."

# 根据环境选择启动方式
if [ "$ENVIRONMENT" = "dev" ]; then
    # 开发环境：使用预构建镜像
    echo "启动开发环境..."
    
    # 检查镜像是否存在
    if ! docker images | grep -q "$IMAGE_NAME"; then
        echo "开发镜像不存在，请先运行: docker build -f Dockerfile.dev -t $IMAGE_NAME ."
        exit 1
    fi
    
    docker run --network=host -d \
      --name $SERVICE_NAME \
      -v $CURRENT_DIR/:/app/ \
      $IMAGE_NAME \
      python app.py
    
    WAIT_TIME=5
else
    # 生产环境：使用预构建的生产镜像
    echo "启动生产环境..."
    
    # 检查镜像是否存在
    if ! docker images | grep -q "$IMAGE_NAME"; then
        echo "生产镜像不存在，请先运行: docker build -f Dockerfile.prod -t $IMAGE_NAME ."
        exit 1
    fi
    
    docker run --network=host -d \
      --name $SERVICE_NAME \
      -e FLASK_ENV=production \
      -e PYTHONUNBUFFERED=1 \
      -v $CURRENT_DIR/:/app/ \
      $IMAGE_NAME \
      python app.py
    
    WAIT_TIME=5
fi

# 等待容器启动
echo "等待容器启动..."
sleep $WAIT_TIME

# 检查容器状态
if docker ps | grep $SERVICE_NAME > /dev/null; then
    echo "✓ 容器启动成功"
    echo "容器名称: $SERVICE_NAME"
    echo "服务地址: http://localhost:10250"
    echo "环境: $ENVIRONMENT"
    echo ""
    echo "查看容器日志: docker logs $SERVICE_NAME"
    echo "进入容器: docker exec -it $SERVICE_NAME bash"
    echo "停止容器: docker stop $SERVICE_NAME"
    echo "删除容器: docker rm $SERVICE_NAME"
else
    echo "✗ 容器启动失败"
    echo "查看日志: docker logs $SERVICE_NAME"
    exit 1
fi

echo "========================================"
echo "启动完成"
echo "========================================"
