# 使用Python 3.12作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 设置环境变量默认值（可在运行时覆盖）
ENV ADMIN_USERNAME=admin \
    ADMIN_PASSWORD=admin \
    JWT_SECRET=your-secret-key

# 暴露端口
EXPOSE 7389

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7389"]
