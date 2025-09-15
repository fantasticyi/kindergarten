# 使用官方Python运行时作为基础镜像
FROM python:3.10.16-slim

# 设置工作目录
WORKDIR /app

# 1. 先仅复制依赖文件（利用缓存）
COPY requirements.txt .

# 安装项目依赖
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 2. 再复制所有代码
COPY . .

# 暴露Flask默认端口
EXPOSE 8080

# 运行应用
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "manage:app"]