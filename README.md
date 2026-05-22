# Clinical Trial Tracker — Description and Deployment Guide

## What is this app?

- This application ingests clinical trial data from the clinicaltrial.gov website, cleans it, and embeds the data with associated vectors for use in LLM queries.
- It then loads this data into a DynamoDB table.
- This data is then shown to the end user in the form of a streamlit dashboard and LLM chatbot trial tracking application.


## Prerequisites

- AWS CLI configured with valid credentials
- Terraform installed
- Docker installed and running

## Steps

### 1. Provision the infrastructure

From the `iac/` directory:

```bash
terraform init
terraform apply
```

Review the plan and type `yes` to confirm.

### 2. Build and push the pipeline image

From the `pipeline/` directory:

```bash
bash push_lambda_to_ecr.sh
```

This builds the Lambda Docker image and pushes it to ECR.

### 3. Build and push the dashboard image

From the `dashboard/` directory:

```bash
bash push_dashboard_to_ecr.sh
```

This builds the Streamlit dashboard image and pushes it to ECR.

### 4. Access the dashboard

1. Open the AWS Console and go to **ECS**.
2. Select the **c23-ecs-cluster** cluster.
3. Go to the **Tasks** tab.
4. Search for **c23-abyssopelagic-dashboard**.
5. Click the running task.
6. Under **Networking**, copy the **Public IP**.
7. Paste it into your browser with port `8501`:

```
http://<public-ip>:8501
```