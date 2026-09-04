pipeline {
    agent any

    environment {
        IMAGE_NAME = 'cake-shop'
        IMAGE_TAG = "${env.BUILD_NUMBER}"
        PATH = "/Users/js/.docker/bin:/usr/local/bin:${env.PATH}"
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    stages {
        stage('Build'){
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .'
                sh 'docker images ${IMAGE_NAME}'
            }
        }

        stage('Test') {
            steps {
                sh 'mkdir -p reports'
                sh '''
                    docker run --rm \
                        -v $WORKSPACE/reports:/app/reports \
                        ${IMAGE_NAME}:${IMAGE_TAG} \
                        pytest cakehome/tests \
                            --junitxml=/app/reports/junit.xml \
                            --cov=cakehome --cov-report=xml:/app/reports/coverage.xml \
                            --cov-fail-under=80
                '''
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }
    }
    post {
        always {
            sh 'docker image prune -f || true'
        }
    }
}