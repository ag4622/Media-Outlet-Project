AWS_REGION="eu-west-2"
AWS_ACCOUNT_ID="129033205317"
REPO_NAME="c23-abyssopelagic-dashboard-ecr"
IMAGE_TAG="latest"
PLATFORM="linux/amd64"

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

aws ecr get-login-password --region $AWS_REGION | \
docker login --username AWS --password-stdin $ECR_URI

docker build -t $REPO_NAME --platform=$PLATFORM --provenance=false .

docker tag ${REPO_NAME}:${IMAGE_TAG} \
${ECR_URI}/${REPO_NAME}:${IMAGE_TAG}

docker push ${ECR_URI}/${REPO_NAME}:${IMAGE_TAG}