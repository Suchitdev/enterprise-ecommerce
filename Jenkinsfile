pipeline {
    agent any

    environment {
        IMAGE_NAME = 'enterprise-ecommerce'
        IMAGE_TAG = "jenkins-${BUILD_NUMBER}"
        DB_CONTAINER = 'jenkins-enterprise-ecommerce-db'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    docker build \
                      -t ${IMAGE_NAME}:${IMAGE_TAG} \
                      .
                '''
            }
        }

        stage('Start Test Database') {
            steps {
                sh '''
                    docker rm -f ${DB_CONTAINER} 2>/dev/null || true

                    docker run -d \
                      --name ${DB_CONTAINER} \
                      -e POSTGRES_DB=enterprise_ecommerce \
                      -e POSTGRES_USER=enterprise_user \
                      -e POSTGRES_PASSWORD=enterprise_password \
                      postgres:16

                    echo "Waiting for PostgreSQL..."

                    sleep 10
                '''
            }
        }

        stage('Run Django Tests') {
            steps {
                sh '''
                    docker run --rm \
                      --link ${DB_CONTAINER}:db \
                      -e POSTGRES_DB=enterprise_ecommerce \
                      -e POSTGRES_USER=enterprise_user \
                      -e POSTGRES_PASSWORD=enterprise_password \
                      -e POSTGRES_HOST=db \
                      -e POSTGRES_PORT=5432 \
                      ${IMAGE_NAME}:${IMAGE_TAG} \
                      python manage.py test
                '''
            }
        }

        stage('Verify Docker Image') {
            steps {
                sh '''
                    docker images ${IMAGE_NAME}
                '''
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f ${DB_CONTAINER} 2>/dev/null || true
                docker image prune -f
            '''
        }

        success {
            echo 'Jenkins CI pipeline completed successfully!'
        }

        failure {
            echo 'Jenkins CI pipeline failed.'
        }
    }
}