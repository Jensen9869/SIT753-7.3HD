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
                sh 'docker build --provenance=false --sbom=false -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest .'
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
                        bandit -r . -l --exclude ./cakehome/tests || true
                '''

                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        -v $WORKSPACE/reports:/reports \
                        aquasec/trivy:latest image \
                            --severity HIGH,CRITICAL \
                            --format json -o /reports/trivy.json \
                            ${IMAGE_NAME}:${IMAGE_TAG} || true
                '''

                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy:latest image \
                            --severity HIGH,CRITICAL \
                            ${IMAGE_NAME}:${IMAGE_TAG} || true
                '''
                                
                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy:latest image \
                            --severity HIGH,CRITICAL \
                            --ignore-unfixed \
                            --pkg-types library \
                            --scanners vuln \
                            --exit-code 0 \
                            ${IMAGE_NAME}:${IMAGE_TAG} || true
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'reports/bandit.json,reports/trivy.json',
                                     allowEmptyArchive: true
                }
            }
        }

        stage('Deploy to Staging') {
            steps {
                sh 'docker compose -f docker-compose.staging.yml -p cakeshop-staging down --remove-orphans || true'
                sh 'IMAGE_TAG=${IMAGE_TAG} docker compose -f docker-compose.staging.yml -p cakeshop-staging up -d'

                sh '''
                    for i in $(seq 1 30); do
                        if curl -fs http://localhost:8001/health/ > /dev/null 2>&1; then
                            echo "Staging is healthy after ${i} attempts"
                            exit 0
                        fi
                        echo "Waiting for staging... (${i}/30)"
                        sleep 2
                    done
                    echo "Staging failed to become healthy"
                    docker compose -f docker-compose.staging.yml -p cakeshop-staging logs web --tail 50
                    exit 1
                '''
            }
        }

        stage('Smoke Test Staging') {
            steps {
                sh 'curl -fs http://localhost:8001/health/ | tee reports/staging-health.json'
                sh 'echo'
                sh 'curl -fs http://localhost:8001/api/cakes/ > /dev/null && echo "API responding"'
                sh 'curl -fs http://localhost:8001/metrics > /dev/null && echo "Metrics exposed"'
            }
        }

        stage('Release') {
            steps {
                script {
                    def version = "v1.0.${env.BUILD_NUMBER}"
                    echo "Releasing ${version}"

                    sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:${version}"
                    sh "docker images ${IMAGE_NAME}"

                    sh "IMAGE_TAG=${version} docker compose -f docker-compose.prod.yml -p cakeshop-prod up -d"

                    sh '''
                        for i in $(seq 1 30); do
                            if curl -fs http://localhost:8002/health/ > /dev/null 2>&1; then
                                echo "Production is healthy after ${i} attempts"
                                exit 0
                            fi
                            echo "Waiting for production... (${i}/30)"
                            sleep 2
                        done
                        echo "Production failed to become healthy"
                        docker compose -f docker-compose.prod.yml -p cakeshop-prod logs web --tail 50
                        exit 1
                    '''

                    sh "echo '${version}' > reports/released-version.txt"
                    sh "curl -fs http://localhost:8002/health/"
                }
            }
            post {
                success {
                    archiveArtifacts artifacts: 'reports/released-version.txt'
                }
            }
        }

    }
    post {
        always {
            sh '''
                docker images ${IMAGE_NAME} --format "{{.Tag}}" \
                    | grep -E "^[0-9]+$" | sort -rn | tail -n +4 \
                    | xargs -I {} docker rmi ${IMAGE_NAME}:{} 2>/dev/null || true
            '''

            sh 'docker image prune -f || true'
        }
    }
}