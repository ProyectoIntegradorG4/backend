#!/bin/bash

# Configuración Simple de Despliegue Docker en AWS
# Este script configura los recursos mínimos de AWS necesarios para el despliegue Docker

set -e

echo "🚀 Configuración Simple de Despliegue Docker en AWS"
echo "=================================================="

# Verificar prerrequisitos
check_prerequisites() {
    echo "📋 Verificando prerrequisitos..."
    
    if ! command -v aws &> /dev/null; then
        echo "❌ AWS CLI no está instalado. Por favor instálalo primero."
        echo "   Visita: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        echo "❌ AWS CLI no está configurado. Por favor ejecuta 'aws configure' primero."
        exit 1
    fi
    
    echo "✅ ¡Verificación de prerrequisitos completada!"
}

# Obtener información de cuenta AWS
get_aws_info() {
    echo "🔍 Obteniendo información de cuenta AWS..."
    
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=$(aws configure get region)
    
    echo "   ID de Cuenta: $AWS_ACCOUNT_ID"
    echo "   Región: $AWS_REGION"
}

# Crear repositorios ECR
create_ecr_repos() {
    echo "📦 Creando repositorios ECR..."

    services=("nit-validation-service" "user-service" "audit-service" "auth-service" "product-service")
    
    for service in "${services[@]}"; do
        echo "Creando repositorio ECR para $service..."
        aws ecr create-repository \
            --repository-name "$service" \
            --region "$AWS_REGION" \
            --image-scanning-configuration scanOnPush=true \
            --encryption-configuration encryptionType=AES256 \
            2>/dev/null || echo "El repositorio $service ya existe"
    done
}

# Crear cluster ECS
create_ecs_cluster() {
    echo "🏗️ Creando cluster ECS..."
    
    aws ecs create-cluster \
        --cluster-name microservices-cluster \
        --capacity-providers FARGATE \
        --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
        --region "$AWS_REGION" \
        2>/dev/null || echo "El cluster microservices-cluster ya existe"
}

# Crear grupos de logs CloudWatch
create_log_groups() {
    echo "📝 Creando grupos de logs CloudWatch..."
    
    services=("nit-validation-service" "user-service" "audit-service" "auth-service" "product-service")

    for service in "${services[@]}"; do
        aws logs create-log-group \
            --log-group-name "/ecs/$service" \
            --region "$AWS_REGION" \
            2>/dev/null || echo "El grupo de logs /ecs/$service ya existe"
    done
}

# Crear instancia RDS PostgreSQL
create_rds() {
    echo "🗄️ Creando instancia RDS PostgreSQL..."
    
    # Verificar si la instancia RDS ya existe
    if aws rds describe-db-instances --db-instance-identifier microservices-db --region "$AWS_REGION" &> /dev/null; then
        echo "La instancia RDS microservices-db ya existe"
        return
    fi
    
    # Obtener VPC por defecto
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region "$AWS_REGION")
    
    # Crear security group para RDS
    SG_ID=$(aws ec2 create-security-group \
        --group-name microservices-rds-sg \
        --description "Security group para RDS de microservicios" \
        --vpc-id "$VPC_ID" \
        --region "$AWS_REGION" \
        --query "GroupId" --output text 2>/dev/null || \
        aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=microservices-rds-sg" \
        --query "SecurityGroups[0].GroupId" --output text --region "$AWS_REGION")
    
    # Obtener subnets para el grupo de subnets RDS
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --query "Subnets[*].SubnetId" --output text --region "$AWS_REGION")
    
    # Crear grupo de subnets DB
    aws rds create-db-subnet-group \
        --db-subnet-group-name microservices-subnet-group \
        --db-subnet-group-description "Grupo de subnets para microservicios" \
        --subnet-ids $SUBNET_IDS \
        --region "$AWS_REGION" \
        2>/dev/null || echo "El grupo de subnets DB ya existe"
    
    # Crear instancia RDS
    aws rds create-db-instance \
        --db-instance-identifier microservices-db \
        --db-instance-class db.t3.micro \
        --engine postgres \
        --engine-version 16.0 \
        --master-username postgres \
        --master-user-password "Microservices123!" \
        --allocated-storage 20 \
        --vpc-security-group-ids "$SG_ID" \
        --db-subnet-group-name microservices-subnet-group \
        --backup-retention-period 7 \
        --skip-final-snapshot \
        --region "$AWS_REGION"
    
    echo "✅ Instancia RDS creada. El endpoint estará disponible en unos minutos."
}

# Crear cluster ElastiCache Redis
create_redis() {
    echo "🔴 Creando cluster ElastiCache Redis..."
    
    # Verificar si el cluster Redis ya existe
    if aws elasticache describe-replication-groups --replication-group-id microservices-redis --region "$AWS_REGION" &> /dev/null; then
        echo "El cluster Redis microservices-redis ya existe"
        return
    fi
    
    # Obtener VPC por defecto
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region "$AWS_REGION")
    
    # Crear security group para Redis
    SG_ID=$(aws ec2 create-security-group \
        --group-name microservices-redis-sg \
        --description "Security group para Redis de microservicios" \
        --vpc-id "$VPC_ID" \
        --region "$AWS_REGION" \
        --query "GroupId" --output text 2>/dev/null || \
        aws ec2 describe-security-groups \
        --filters "Name=group-name,Values=microservices-redis-sg" \
        --query "SecurityGroups[0].GroupId" --output text --region "$AWS_REGION")
    
    # Obtener subnets para el grupo de subnets Redis
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" \
        --query "Subnets[*].SubnetId" --output text --region "$AWS_REGION")
    
    # Crear grupo de subnets cache
    aws elasticache create-cache-subnet-group \
        --cache-subnet-group-name microservices-cache-subnet-group \
        --cache-subnet-group-description "Grupo de subnets para cache de microservicios" \
        --subnet-ids $SUBNET_IDS \
        --region "$AWS_REGION" \
        2>/dev/null || echo "El grupo de subnets cache ya existe"
    
    # Crear cluster Redis
    aws elasticache create-replication-group \
        --replication-group-id microservices-redis \
        --description "Cluster Redis para microservicios" \
        --node-type cache.t3.micro \
        --port 6379 \
        --num-cache-clusters 1 \
        --subnet-group-name microservices-cache-subnet-group \
        --security-group-ids "$SG_ID" \
        --region "$AWS_REGION"
    
    echo "✅ Cluster Redis creado. El endpoint estará disponible en unos minutos."
}

# Instrucciones de secretos de GitHub
github_secrets_instructions() {
    echo ""
    echo "🔐 Instrucciones de Configuración de Secretos de GitHub"
    echo "======================================================"
    echo ""
    echo "1. Ve a tu repositorio de GitHub"
    echo "2. Navega a Settings → Secrets and variables → Actions"
    echo "3. Agrega los siguientes secretos:"
    echo ""
    echo "   AWS_ACCESS_KEY_ID: $(aws configure get aws_access_key_id)"
    echo "   AWS_SECRET_ACCESS_KEY: [Tu AWS Secret Access Key]"
    echo "   RDS_ENDPOINT: [Estará disponible después de crear RDS]"
    echo "   REDIS_ENDPOINT: [Estará disponible después de crear Redis]"
    echo "   POSTGRES_PASSWORD: Microservices123!"
    echo "   JWT_SECRET_KEY: your-super-secret-jwt-key-change-in-production-2024"
    echo ""
    echo "4. Obtener el endpoint de RDS:"
    echo "   aws rds describe-db-instances --db-instance-identifier microservices-db --query 'DBInstances[0].Endpoint.Address' --output text"
    echo ""
    echo "5. Obtener el endpoint de Redis:"
    echo "   aws elasticache describe-replication-groups --replication-group-id microservices-redis --query 'ReplicationGroups[0].PrimaryEndpoint.Address' --output text"
    echo ""
}

# Ejecución principal
main() {
    check_prerequisites
    get_aws_info
    create_ecr_repos
    create_ecs_cluster
    create_log_groups
    create_rds
    create_redis
    github_secrets_instructions
    
    echo ""
    echo "🎉 ¡Configuración completada exitosamente!"
    echo ""
    echo "Próximos pasos:"
    echo "1. Espera 5-10 minutos para que RDS y Redis estén listos"
    echo "2. Configura los secretos de GitHub como se indicó arriba"
    echo "3. Inicializa la base de datos con: psql -h [RDS_ENDPOINT] -U postgres -d postgres -f 001-init.sql"
    echo "4. Haz push de tu código a la rama main para activar el despliegue"
    echo ""
    echo "¡Tus microservicios se desplegarán automáticamente!"
}

# Ejecutar función principal
main "$@"
