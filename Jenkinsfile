/* ============================================================
 * CICD 演示项目的 Jenkins 流水线（完整 CI/CD）
 *
 * 阶段说明：
 *   1. Checkout     —— 从 Git 拉取代码
 *   2. Install      —— 创建虚拟环境并安装依赖
 *   3. Test         —— 运行 pytest，生成 JUnit 报告
 *   4. Docker Build —— 构建镜像，直接使用私有仓库前缀
 *   5. Push         —— 推送镜像到私有 Registry
 *   6. Deploy       —— SSH 到目标机执行部署脚本
 *   7. Smoke Test   —— 部署后访问 /health 验证服务可用
 *
 * 前置条件：
 *   - Jenkins 容器可访问 192.168.17.129:5000（私有 registry）
 *   - Jenkins 凭据 deploy-ssh 中存有目标机私钥
 *   - 目标机 /data/cicd-demo/deploy.sh 已就绪
 * ============================================================ */

pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        REGISTRY    = '192.168.17.129:5000'          // 私有镜像仓库地址
        IMAGE_NAME  = 'cicd-demo'                    // 镜像名
        IMAGE_TAG   = "${env.BUILD_NUMBER}"          // 用构建号做 tag，唯一且可回滚
        FULL_IMAGE  = "${REGISTRY}/${IMAGE_NAME}"    // 完整镜像地址
        DEPLOY_HOST = '192.168.17.130'               // 目标机 IP
        DEPLOY_DIR  = '/data/cicd-demo'              // 目标机部署目录
        VENV        = '.venv'                        // 虚拟环境目录
    }

    stages {

        /* ---------- 1. 拉取代码 ---------- */
        stage('Checkout') {
            steps {
                checkout scm
                sh 'git log -1 --pretty=format:"commit: %h %s%n"'
            }
        }

        /* ---------- 2. 安装依赖 ---------- */
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

        /* ---------- 3. 单元测试 ---------- */
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

        /* ---------- 4. 构建镜像 ---------- */
        stage('Docker Build') {
            steps {
                sh '''
                    set -e
                    docker build -t $FULL_IMAGE:$IMAGE_TAG -t $FULL_IMAGE:latest .
                    docker images | grep $IMAGE_NAME
                '''
            }
        }

        /* ---------- 5. 推送镜像 ---------- */
        stage('Push') {
            steps {
                sh '''
                    set -e
                    docker push $FULL_IMAGE:$IMAGE_TAG
                    docker push $FULL_IMAGE:latest
                '''
            }
        }

        /* ---------- 6. 部署到目标机 ---------- */
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

        /* ---------- 7. 部署后健康检查 ---------- */
        stage('Smoke Test') {
            steps {
                sh '''
                    set -e
                    # 等待容器启动，最多重试 10 次（每次间隔 3 秒）
                    curl -fsS --retry 10 --retry-delay 3 \
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
