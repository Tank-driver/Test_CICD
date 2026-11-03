/* ============================================================
 * CICD 演示项目的 Jenkins 流水线
 *
 * 阶段说明：
 *   1. Checkout     —— 从 Git 拉取代码
 *   2. Install      —— 创建虚拟环境并安装依赖
 *   3. Test         —— 运行 pytest，生成 JUnit 报告
 *   4. Docker Build —— 构建 Docker 镜像，tag 使用构建号
 *
 * 说明：Jenkins 运行在 Docker 容器中，通过挂载的
 *       /var/run/docker.sock 调用宿主机 Docker，所以这里
 *       可以直接执行 docker 命令。
 * ============================================================ */

pipeline {
    // 不指定标签，使用 Jenkins 内置节点执行
    agent any

    options {
        timestamps()                                    // 每行日志前加时间戳，方便排查耗时
        timeout(time: 20, unit: 'MINUTES')              // 整条流水线最长 20 分钟，超时自动终止
        buildDiscarder(logRotator(numToKeepStr: '10'))  // 只保留最近 10 次构建，防止磁盘占满
    }

    environment {
        IMAGE_NAME = 'cicd-demo'                        // 镜像名
        IMAGE_TAG  = "${env.BUILD_NUMBER}"              // 用构建号做 tag，天然唯一且可追溯
        VENV       = '.venv'                            // 虚拟环境目录（已在 .gitignore 中排除）
    }

    stages {

        /* ---------- 1. 拉取代码 ---------- */
        stage('Checkout') {
            steps {
                checkout scm                                // 按任务里配置的 SCM 拉代码
                sh 'git log -1 --pretty=format:"commit: %h %s%n"'   // 打印当前提交，便于对照发布版本
            }
        }

        /* ---------- 2. 安装依赖 ---------- */
        stage('Install') {
            steps {
                sh '''
                    set -e
                    python3 --version
                    # 创建隔离的虚拟环境，避免污染容器全局 Python
                    # （Debian 13 默认禁用系统级 pip install，必须用 venv）
                    python3 -m venv $VENV
                    . $VENV/bin/activate
                    # 使用清华源加速；国内环境必备，否则容易超时
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
                    # --junitxml 生成 JUnit 格式报告，供 Jenkins 解析展示
                    pytest -v --junitxml=report.xml
                '''
            }
            post {
                always {
                    // 无论成功失败都归档测试报告，失败时也能看到哪些用例挂了
                    junit 'report.xml'
                }
            }
        }

        /* ---------- 4. 构建镜像 ---------- */
        stage('Docker Build') {
            steps {
                sh '''
                    set -e
                    # 同时打两个 tag：构建号（精确版本）+ latest（方便部署时直接引用）
                    docker build -t $IMAGE_NAME:$IMAGE_TAG -t $IMAGE_NAME:latest .
                    docker images $IMAGE_NAME
                '''
            }
        }
    }

    post {
        success {
            echo "✅ 构建成功：${IMAGE_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo "❌ 构建失败，查看日志：${env.BUILD_URL}console"
        }
    }
}
