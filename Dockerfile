# 使用官方的 Python 3.9 slim 镜像
FROM python:3.9-slim

# 在容器内创建一个工作目录
WORKDIR /app

# 1. 复制依赖文件
# 注意路径变化：现在需要指定从 back/kindergarten/ 复制
COPY back/kindergarten/requirements.txt ./

# 2. 安装所有依赖 (使用清华镜像源加速)
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 复制所有项目文件到工作目录
# 注意路径变化：将 back/kindergarten/ 目录下的所有内容复制到容器的 /app 目录
COPY back/kindergarten/ .

# 4. 暴露容器的 80 端口，供云托管平台使用
EXPOSE 80

# 5. 启动 Gunicorn 服务器
# Gunicorn 会在 /app 目录里寻找 manage:app
CMD ["gunicorn", "manage:app", "--bind", "0.0.0.0:80", "--workers", "4"]