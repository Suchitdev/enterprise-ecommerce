pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "suchit10/enterprise-ecommerce"

        // EC2 deployment details
        EC2_HOST = "13.207.181.55"
        EC2_USER = "ubuntu"
        SSH_KEY = "/tmp/github-actions-dockerhub-cd.pem"

        // Application settings
        CONTAINER_NAME = "enterprise-web"
        DB_CONTAINER = "enterprise-db"
        DOCKER_NETWORK = "enterprise-network"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh """
                    docker build \
                        -t ${DOCKER_IMAGE}:jenkins-${BUILD_NUMBER} \
                        -t ${DOCKER_IMAGE}:latest \
                        .
                """
            }
        }

        stage('Run Django Tests') {
            steps {
                sh """
                    docker run --rm \
                        --network jenkins-test \
                        -e POSTGRES_DB=enterprise_ecommerce \
                        -e POSTGRES_USER=enterprise_user \
                        -e POSTGRES_PASSWORD=enterprise_password \
                        -e POSTGRES_HOST=jenkins-db \
                        -e POSTGRES_PORT=5432 \
                        ${DOCKER_IMAGE}:jenkins-${BUILD_NUMBER} \
                        python manage.py test
                """
            }
        }

        stage('Docker Hub Login & Push') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {
                    sh """
                        echo "\$DOCKER_PASSWORD" | docker login \
                            -u "\$DOCKER_USERNAME" \
                            --password-stdin

                        docker push ${DOCKER_IMAGE}:jenkins-${BUILD_NUMBER}
                        docker push ${DOCKER_IMAGE}:latest

                        docker logout
                    """
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                sh """
                    docker exec jenkins ssh \
                        -i ${SSH_KEY} \
                        -o StrictHostKeyChecking=no \
                        ${EC2_USER}@${EC2_HOST} '
                        
                        set -e

                        echo "===== Pulling latest Docker image ====="

                        docker pull ${DOCKER_IMAGE}:latest


                        echo "===== Creating Docker network if needed ====="

                        docker network inspect ${DOCKER_NETWORK} >/dev/null 2>&1 || \
                        docker network create ${DOCKER_NETWORK}


                        echo "===== Checking PostgreSQL container ====="

                        if ! docker ps --format "{{.Names}}" | grep -q "^${DB_CONTAINER}\$"; then

                            if docker ps -a --format "{{.Names}}" | grep -q "^${DB_CONTAINER}\$"; then
                                echo "Starting existing PostgreSQL container..."
                                docker start ${DB_CONTAINER}
                            else
                                echo "Creating PostgreSQL container..."

                                docker run -d \
                                    --name ${DB_CONTAINER} \
                                    --network ${DOCKER_NETWORK} \
                                    -e POSTGRES_DB=enterprise_ecommerce \
                                    -e POSTGRES_USER=enterprise_user \
                                    -e POSTGRES_PASSWORD=enterprise_password \
                                    -v enterprise_postgres_data:/var/lib/postgresql/data \
                                    --restart unless-stopped \
                                    postgres:16
                            fi

                        else
                            echo "PostgreSQL is already running."
                        fi


                        echo "===== Waiting for PostgreSQL ====="

                        sleep 5


                        echo "===== Removing old application container ====="

                        docker rm -f ${CONTAINER_NAME} 2>/dev/null || true


                        echo "===== Starting new application container ====="

                        docker run -d \
                            --name ${CONTAINER_NAME} \
                            --network ${DOCKER_NETWORK} \
                            -p 8000:8000 \
                            -e POSTGRES_DB=enterprise_ecommerce \
                            -e POSTGRES_USER=enterprise_user \
                            -e POSTGRES_PASSWORD=enterprise_password \
                            -e POSTGRES_HOST=${DB_CONTAINER} \
                            -e POSTGRES_PORT=5432 \
                            -e ALLOWED_HOSTS=${EC2_HOST},localhost,127.0.0.1 \
                            --restart unless-stopped \
                            ${DOCKER_IMAGE}:latest


                        echo "===== Running Django migrations ====="

                        docker exec ${CONTAINER_NAME} \
                            python manage.py migrate --noinput


                        echo "===== Checking product count ====="

                        PRODUCT_COUNT=\$(docker exec ${CONTAINER_NAME} \
                            python manage.py shell -c \
                            "from products.models import Product; print(Product.objects.count())" \
                            | tail -1)

                        echo "Current product count: \$PRODUCT_COUNT"


                        if [ "\$PRODUCT_COUNT" -eq 0 ]; then

                            echo "===== Database is empty ====="
                            echo "===== Importing 200 products from API ====="

                            docker exec ${CONTAINER_NAME} \
                                python manage.py import_products \
                                --source api \
                                --limit 200

                        else

                            echo "===== Products already exist ====="
                            echo "===== Skipping product import ====="

                        fi


                        echo "===== Restarting application ====="

                        docker restart ${CONTAINER_NAME}


                        echo "===== Deployment completed ====="

                        docker ps --filter "name=${CONTAINER_NAME}"

                        echo "===== Application logs ====="

                        docker logs ${CONTAINER_NAME} --tail 20
                    '
                """
            }
        }

        stage('Verify Deployment') {
            steps {
                sh """
                    docker exec jenkins ssh \
                        -i ${SSH_KEY} \
                        -o StrictHostKeyChecking=no \
                        ${EC2_USER}@${EC2_HOST} \
                        "curl -f http://localhost:8000 >/dev/null && echo 'Application is LIVE successfully!'"
                """
            }
        }
    }

    post {
        success {
            echo '=============================================='
            echo ' Jenkins CI/CD Pipeline Completed Successfully'
            echo '=============================================='
            echo "Docker Image: ${DOCKER_IMAGE}:latest"
            echo "Website: http://${EC2_HOST}:8000"
        }

        failure {
            echo '=============================================='
            echo ' Jenkins CI/CD Pipeline FAILED'
            echo '=============================================='
            echo 'Check the failed stage and console output.'
        }
    }
}