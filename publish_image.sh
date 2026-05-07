#!/bin/bash
# Sagittarius 镜像发布脚本

# 1. 配置参数 (请修改为您的实际信息)
REGISTRY_USER="ethanouyang"
IMAGE_NAME="sagittarius"
TAG="latest"
FULL_IMAGE_NAME="${REGISTRY_USER}/${IMAGE_NAME}:${TAG}"

echo "🚀 开始构建镜像: ${FULL_IMAGE_NAME}..."

# 2. 构建镜像
docker build --pull -t "${FULL_IMAGE_NAME}" -f .devcontainer/Dockerfile .

if [ $? -eq 0 ]; then
    echo "✅ 镜像构建成功！"
else
    echo "❌ 镜像构建失败，请检查 Dockerfile。"
    exit 1
fi

# 3. 推送镜像
echo "🔑 准备推送镜像..."
docker push "${FULL_IMAGE_NAME}"

if [ $? -eq 0 ]; then
    echo "🎉 推送完成！协作者现在可以通过以下命令拉取："
    echo "docker pull ${FULL_IMAGE_NAME}"
else
    echo "❌ 推送失败，请确保已执行 'docker login' 并具有权限。"
    exit 1
fi
