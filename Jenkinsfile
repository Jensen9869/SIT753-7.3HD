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
                            --cov=. --cov-report=xml:/app/reports/coverage.xml \
                            --cov-fail-under=80
                '''
                sh "sed -i.bak 's|<source>/app</source>|<source>backend</source>|' reports/coverage.xml || true"
            }
            post {
                always {
                    junit 'reports/junit.xml'
                }
            }
        }

        stage('Code Quality') {
            steps {
                script {
                    def scannerHome = tool 'SonarScanner'
                    withSonarQubeEnv('SonarQube') {
                        sh "cd backend && ${scannerHome}/bin/sonar-scanner"
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Security') {
            steps {
                sh 'mkdir -p reports'

                sh '''
                    docker run --rm \
                        -v $WORKSPACE/reports:/app/reports \
                        ${IMAGE_NAME}:${IMAGE_TAG} \
                        bandit -r . -f json -o /app/reports/bandit.json \
                            --exclude ./cakehome/tests || true
                '''
                sh '''
                    docker run --rm ${IMAGE_NAME}:${IMAGE_TAG} \
                        bandit -r . -ll --exclude ./cakehome/tests || true
                '''

                sh 'trivy image --severity HIGH,CRITICAL --format json \
                        -o reports/trivy.json ${IMAGE_NAME}:${IMAGE_TAG} || true'
                sh 'trivy image --severity HIGH,CRITICAL ${IMAGE_NAME}:${IMAGE_TAG} || true'
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/bandit.json,reports/trivy.json',
                                     allowEmptyArchive: true
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