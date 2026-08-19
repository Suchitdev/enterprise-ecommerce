pipeline {
    agent any

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
                      -t enterprise-ecommerce:jenkins-${BUILD_NUMBER} \
                      .
                '''
            }
        }

        stage('Verify Docker Image') {
            steps {
                sh '''
                    docker images enterprise-ecommerce
                '''
            }
        }
    }

    post {
        success {
            echo 'Jenkins CI pipeline completed successfully!'
        }

        failure {
            echo 'Jenkins CI pipeline failed.'
        }
    }
}