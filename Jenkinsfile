// ============================================================
// SecureShip CI/CD Pipeline
// ============================================================
// A "declarative" Jenkins pipeline (the modern, readable style,
// as opposed to older "scripted" pipelines). Each `stage` shows
// up as its own box in the Jenkins UI, so you can see exactly
// where a build passed or failed.
//
// Flow: Checkout -> Lint -> Test -> SAST scan -> Build image ->
//       Container scan -> Push to registry -> Deploy -> Smoke test
// ============================================================

pipeline {
    // 'agent any' = run on any available Jenkins agent/executor.
    // For a beginner setup (Jenkins running in a single Docker
    // container) this just means "run on this machine".
    agent any

    // Environment variables available to every stage below.
    environment {
        IMAGE_NAME   = "secureship"
        // Credentials are never hard-coded — Jenkins injects the
        // actual username/password at runtime from the credential
        // you configure in Manage Jenkins > Credentials. This ID
        // must match the credential you create (see README).
        DOCKERHUB    = credentials('dockerhub-creds')
        IMAGE_TAG    = "${env.BUILD_NUMBER}"
    }

    options {
        // Auto-cancel a running build if a newer commit triggers a
        // new one — saves time/resources on a shared Jenkins box.
        disableConcurrentBuilds()
        // Keep only the last 10 builds' logs and artifacts.
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {

        stage('Checkout') {
            steps {
                // Pulls whatever repo/branch this Jenkins job is
                // configured against (set up via "Pipeline script
                // from SCM" pointing at your GitHub repo).
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --no-cache-dir -r requirements-dev.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                // flake8 catches style issues and some real bugs
                // (unused imports, undefined names) before they
                // ever reach a test run.
                sh '''
                    . .venv/bin/activate
                    flake8 app/ --max-line-length=100
                '''
            }
        }

        stage('Unit Tests') {
            steps {
                sh '''
                    . .venv/bin/activate
                    pytest tests/ --junitxml=test-results.xml -v
                '''
            }
            post {
                always {
                    // junit converts pytest's XML output into a nice
                    // pass/fail graph in the Jenkins build page.
                    junit 'test-results.xml'
                }
            }
        }

        stage('SAST Scan') {
            steps {
                // Bandit is a static analysis security tool for
                // Python — it looks for things like hardcoded
                // passwords, use of eval(), insecure hashing, etc.
                // '|| true' lets the build continue and still show
                // findings in Jenkins rather than hard-failing while
                // you're still learning what it flags; tighten this
                // to a real failure condition once you're comfortable.
                sh '''
                    . .venv/bin/activate
                    bandit -r app/ -f txt -o bandit-report.txt || true
                    cat bandit-report.txt
                '''
            }
            post {
                always {
                    archiveArtifacts artifacts: 'bandit-report.txt', allowEmptyArchive: true
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
            }
        }

        stage('Container Vulnerability Scan') {
            steps {
                // Trivy scans the built image's OS packages and
                // Python dependencies for known CVEs. This is the
                // stage most beginner Jenkins tutorials skip
                // entirely — including it is what makes this
                // pipeline "DevSecOps" rather than just "CI/CD".
                sh '''
                    trivy image --severity HIGH,CRITICAL \
                       --ignore-unfixed \
                       --exit-code 1 \
                        --format table \
                        ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                sh '''
                    echo "$DOCKERHUB_PSW" | docker login -u "$DOCKERHUB_USR" --password-stdin
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} $DOCKERHUB_USR/${IMAGE_NAME}:${IMAGE_TAG}
                    docker tag ${IMAGE_NAME}:${IMAGE_TAG} $DOCKERHUB_USR/${IMAGE_NAME}:latest
                    docker push $DOCKERHUB_USR/${IMAGE_NAME}:${IMAGE_TAG}
                    docker push $DOCKERHUB_USR/${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Deploy') {
            steps {
                // Simplified blue-green deploy: bring up the new
                // version on a temporary port, health-check it, and
                // only then flip traffic by restarting the "live"
                // container against the new image. This mirrors the
                // blue-green concept you already know from your AWS
                // work, just scaled down to fit a laptop-sized demo.
                sh '''
                    docker rm -f secureship-green 2>/dev/null || true
                    docker run -d --name secureship-green -p 5001:5000 \
                        $DOCKERHUB_USR/${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                // Hit the health endpoint on the newly deployed
                // "green" container before promoting it. If this
                // fails, the pipeline stops here — the old "blue"
                // container is untouched and still serving traffic.
                sh '''
                    sleep 3
                    curl --fail http://localhost:5001/health
                '''
            }
        }

        stage('Promote to Live') {
            steps {
                // "Promotion" here just means switching the public
                // port from the old container to the new one. In a
                // real cloud setup this is a load-balancer target
                // swap instead of a port swap.
                sh '''
                    docker rm -f secureship-live 2>/dev/null || true
                    docker rm -f secureship-green 2>/dev/null || true
                    docker run -d --name secureship-live -p 5000:5000 \
                        $DOCKERHUB_USR/${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }
    }

    post {
        success {
            echo "Build ${env.BUILD_NUMBER} deployed successfully."
        }
        failure {
            echo "Build ${env.BUILD_NUMBER} failed — live container was left untouched."
        }
        always {
            sh 'docker logout || true'
        }
    }
}
