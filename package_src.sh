VERSION=$(git rev-parse --short HEAD)
TAG=${VERSION}
ARCHIVE_PATH="deploy_artifacts/version_control_src_${TAG}.tar.gz"
echo "Creating source archive at $ARCHIVE_PATH"
git archive -o "$ARCHIVE_PATH" HEAD