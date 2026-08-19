pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "suchit10/enterprise-ecommerce"
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

        stage('Verify Docker Image') {
            steps {
                sh """
                    docker images ${DOCKER_IMAGE}
                """
            }
        }
    }

    post {
        success {
            echo 'Jenkins CI/CD image build and Docker Hub push completed successfully!'
        }

        failure {
            echo 'Jenkins pipeline failed.'
        }
    }
}