/* ============================================================
 * 单机德州扑克 CI/CD 流水线
 *
 * 1. Checkout  拉代码
 * 2. Install   建虚拟环境装依赖
 * 3. Test      跑 25 个用例（牌型判定 + 游戏流程）
 * 4. Build     构建镜像
 * 5. Push      推送到私有 registry
 * 6. Deploy    SSH 到目标机执行 deploy.sh
 * 7. Smoke     请求 /health 验证
 * ============================================================ */

pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        REGISTRY    = '192.168.17.129:5000'
        IMAGE_NAME  = 'poker'
        IMAGE_TAG   = "${env.BUILD_NUMBER}"
        FULL_IMAGE  = "${REGISTRY}/${IMAGE_NAME}"
        DEPLOY_HOST = '192.168.17.130'
        DEPLOY_DIR  = '/data/cicd-demo'
        VENV        = '.venv'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --pretty=format:"commit: %h %s%n"'
            }
        }

        stage('Install') {
            steps {
                sh '''
                    set -e
                    python3 --version
                    python3 -m venv $VENV
                    . $VENV/bin/activate
                    pip install --no-cache-dir -r requirements.txt \
                        -i https://pypi.tuna.tsinghua.edu.cn/simple
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    set -e
                    . $VENV/bin/activate
                    pytest -v --junitxml=report.xml
                '''
            }
            post {
                always { junit 'report.xml' }
            }
        }

        stage('Build') {
            steps {
                sh '''
                    set -e
                    docker build -t $FULL_IMAGE:$IMAGE_TAG -t $FULL_IMAGE:latest .
                    docker images | grep $IMAGE_NAME
                '''
            }
        }

        stage('Push') {
            steps {
                sh '''
                    set -e
                    docker push $FULL_IMAGE:$IMAGE_TAG
                    docker push $FULL_IMAGE:latest
                '''
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([
                    sshUserPrivateKey(
                        credentialsId: 'deploy-ssh',
                        keyFileVariable: 'SSH_KEY',
                        usernameVariable: 'SSH_USER'
                    )
                ]) {
                    sh '''
                        set -e
                        ssh -i "$SSH_KEY" \
                            -o StrictHostKeyChecking=no \
                            -o UserKnownHostsFile=/dev/null \
                            $SSH_USER@$DEPLOY_HOST \
                            "$DEPLOY_DIR/deploy.sh $FULL_IMAGE $IMAGE_TAG"
                    '''
                }
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    set -e
                    curl -fsS --retry 15 --retry-delay 2 --retry-connrefused \
                        http://$DEPLOY_HOST:8080/health
                    echo ""
                    echo "服务健康检查通过"
                '''
            }
        }
    }

    post {
        success { echo "✅ 部署成功：${FULL_IMAGE}:${IMAGE_TAG} -> ${DEPLOY_HOST}:8080" }
        failure { echo "❌ 失败，查看日志：${env.BUILD_URL}console" }
    }
}
