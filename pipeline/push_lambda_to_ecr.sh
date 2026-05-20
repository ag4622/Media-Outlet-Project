aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 129033205317.dkr.ecr.eu-west-2.amazonaws.com

docker build -t c23-abyssopelagic-lambda-ecr --platform="linux/amd64" --provenance=false .

docker tag c23-abyssopelagic-lambda-ecr:latest 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c23-abyssopelagic-lambda-ecr:latest

docker push 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c23-abyssopelagic-lambda-ecr:latest