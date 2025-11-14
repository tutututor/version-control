#!/bin/bash

# 2. 构建镜像
docker buildx build --platform linux/amd64 \
  -t version-control-service \
  -f Dockerfile.dev .

# 3. 保存镜像到 deploy_artifacts 目录
docker save version-control-service | gzip > deploy_artifacts/version-control-service.tar.gz

echo "镜像已构建: version-control-service"
