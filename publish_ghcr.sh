#!/bin/bash
# Sagittarius GitHub Packages (GHCR) 发布脚本

# 1. 配置参数
GH_USER="Ouyxw"
REPO_NAME="sagittarius" 
TAG="latest"

# 自动转换为小写 (Docker 强制要求镜像名必须全小写)
GH_USER_LOWER=$(echo "$GH_USER" | tr '[:upper:]' '[:lower:]')
REPO_NAME_LOWER=$(echo "$REPO_NAME" | tr '[:upper:]' '[:lower:]')

# GHCR 的完整镜像名称格式必须为: ghcr.io/owner/image-name:tag
FULL_IMAGE_NAME="ghcr.io/${GH_USER_LOWER}/${REPO_NAME_LOWER}:${TAG}"

echo "🚀 准备构建并发布到 GHCR: ${FULL_IMAGE_NAME}..."

# 2. 构建镜像
docker build --pull -t "${FULL_IMAGE_NAME}" -f .devcontainer/Dockerfile .

if [ $? -eq 0 ]; then
    echo "✅ 镜像构建成功！"
else
    echo "❌ 镜像构建失败。"
    exit 1
fi

# 3. 登录并推送
echo "🔑 准备推送镜像到 GHCR..."
echo "提示：如果尚未登录，请运行: echo \$CR_PAT | docker login ghcr.io -u ${GH_USER} --password-stdin"

docker push "${FULL_IMAGE_NAME}"

if [ $? -eq 0 ]; then
    echo "🎉 推送完成！"
    echo "公开镜像拉取命令："
    echo "docker pull ${FULL_IMAGE_NAME}"
else
    echo "❌ 推送失败。请检查您的 PAT 权限是否包含 'write:packages'。"
    exit 1
fi
