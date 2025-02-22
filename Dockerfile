# 第一阶段：构建阶段
FROM python:3.12-alpine AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# 第二阶段：运行阶段
FROM python:3.12-alpine

WORKDIR /app

# 从构建阶段复制已安装的包
COPY --from=builder /install /usr/local

# 仅复制必要的文件
COPY main.py utils.py database.py ./
COPY static/ ./static/

# 设置环境变量默认值
ENV ADMIN_USERNAME=admin \
    ADMIN_PASSWORD=admin \
    JWT_SECRET=your-secret-key

EXPOSE 7389

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7389"]
