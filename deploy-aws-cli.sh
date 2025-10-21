#!/bin/bash

# AWS CLI Direct Deployment Script
# This approach bypasses ECS CLI and uses AWS CLI directly

set -e

echo "🚀 AWS CLI Direct Deployment"
echo "============================"

# Configuration
SERVICE_NAME=$1
ECR_REGISTRY=${ECR_REGISTRY:-"403245568912.dkr.ecr.us-east-1.amazonaws.com"}
AWS_REGION=${AWS_REGION:-"us-east-1"}
CLUSTER_NAME=${CLUSTER_NAME:-"microservices-cluster"}
VPC_ID=${VPC_ID:-"vpc-000db55d9aec78c3c"}
SUBNET_ID=${SUBNET_ID:-"subnet-0bc9724bfda2781c8"}
SECURITY_GROUP_ID=${SECURITY_GROUP_ID:-"sg-062e1b7295652790c"}

if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Error: Service name is required"
    echo "Usage: $0 <service-name>"
    echo "Available services: nit-validation-service, user-service, audit-service, auth-service"
    exit 1
fi

echo "📦 Deploying service: $SERVICE_NAME"
echo "🏗️ ECR Registry: $ECR_REGISTRY"
echo "🌍 Region: $AWS_REGION"
echo "🏢 Cluster: $CLUSTER_NAME"

# Get service configuration
case $SERVICE_NAME in
    "nit-validation-service")
        PORT=8002
        LOG_GROUP="/ecs/nit-validation-service"
        ;;
    "user-service")
        PORT=8001
        LOG_GROUP="/ecs/user-service"
        ;;
    "audit-service")
        PORT=8003
        LOG_GROUP="/ecs/audit-service"
        ;;
    "auth-service")
        PORT=8004
        LOG_GROUP="/ecs/auth-service"
        ;;
    *)
        echo "❌ Error: Unknown service $SERVICE_NAME"
        exit 1
        ;;
esac

echo "🔧 Service configuration:"
echo "   Port: $PORT"
echo "   Log Group: $LOG_GROUP"

# Create log group if it doesn't exist
echo "📝 Creating log group if it doesn't exist..."
aws logs create-log-group \
    --log-group-name "$LOG_GROUP" \
    --region "$AWS_REGION" \
    2>/dev/null || echo "Log group already exists"

# Create task definition
echo "📋 Creating task definition..."
cat > task-definition.json <<EOF
{
    "family": "$SERVICE_NAME",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "256",
    "memory": "512",
    "executionRoleArn": "arn:aws:iam::403245568912:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "$SERVICE_NAME",
            "image": "$ECR_REGISTRY/$SERVICE_NAME:latest",
            "portMappings": [
                {
                    "containerPort": $PORT,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {"name": "POSTGRES_DB", "value": "postgres"},
                {"name": "POSTGRES_USER", "value": "postgres"},
                {"name": "POSTGRES_PASSWORD", "value": "$POSTGRES_PASSWORD"},
                {"name": "POSTGRES_HOST", "value": "$POSTGRES_HOST"},
                {"name": "POSTGRES_PORT", "value": "5432"},
                {"name": "DATABASE_URL", "value": "$DATABASE_URL"},
                {"name": "REDIS_URL", "value": "$REDIS_URL"},
                {"name": "JWT_SECRET_KEY", "value": "$JWT_SECRET_KEY"},
                {"name": "JWT_EXPIRE_MINUTES", "value": "60"}
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "$LOG_GROUP",
                    "awslogs-region": "$AWS_REGION",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "healthCheck": {
                "command": ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:$PORT/health')"],
                "interval": 30,
                "timeout": 10,
                "retries": 3
            }
        }
    ]
}
EOF

# Register task definition
echo "📝 Registering task definition..."
TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://task-definition.json \
    --region "$AWS_REGION" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

echo "✅ Task definition registered: $TASK_DEF_ARN"

# Check if service exists
echo "🔍 Checking if service exists..."
SERVICE_EXISTS=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --region "$AWS_REGION" \
    --query 'services[0].serviceName' \
    --output text 2>/dev/null || echo "None")

if [ "$SERVICE_EXISTS" = "None" ] || [ "$SERVICE_EXISTS" = "" ]; then
    echo "📦 Creating new service..."
    aws ecs create-service \
        --cluster "$CLUSTER_NAME" \
        --service-name "$SERVICE_NAME" \
        --task-definition "$TASK_DEF_ARN" \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=ENABLED}" \
        --region "$AWS_REGION"
    echo "✅ Service created successfully"
else
    echo "🔄 Updating existing service..."
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --task-definition "$TASK_DEF_ARN" \
        --region "$AWS_REGION"
    echo "✅ Service updated successfully"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "📋 Service: $SERVICE_NAME"
echo "🌐 Port: $PORT"
echo "📊 Task Definition: $TASK_DEF_ARN"
echo ""
echo "🔍 To check service status:"
echo "   aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME --region $AWS_REGION"

# Cleanup
rm -f task-definition.json
