pipeline {
    agent any

    environment {
        PROJECT_ID = 'ai-detector-pipeline'
        REGION = 'us-central1'
        REPO = 'ai-detector-repo' 
        IMAGE_NAME = 'ai-detector'
        GAR_URL = "${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}"
        CREDENTIALS_ID = 'gcp-artifact' 
    }

    stages {
        stage('Checkout') {
            steps {
                git credentialsId: 'github', url: 'https://github.com/ashah-004/MCP-ML-PIPELINE.git', branch: 'main'
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    sh 'docker build -t $IMAGE_NAME .'
                }
            }
        }

        stage('Docker Tag & Push to GAR') {
            steps {
                withCredentials([file(credentialsId: "${CREDENTIALS_ID}", variable: 'GOOGLE_APPLICATION_CREDENTIALS')]) {
                    sh '''
                        gcloud auth activate-service-account --key-file=$GOOGLE_APPLICATION_CREDENTIALS
                        gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet
                        docker tag $IMAGE_NAME $GAR_URL
                        docker push $GAR_URL
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sshagent(['vm2-ssh-credentials']) {
                    sh '''
                        scp -r k8s/ ashah004@34.94.241.11:/tmp/k8s
                        ssh ashah004@34.94.241.11 "
                        kubectl apply -f /tmp/k8s &&
                        rm -rf /tmp/k8s
                        "
                    '''
                }
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully!'
        }
        failure {
            echo '❌ Pipeline failed.'
        }
    }
}
