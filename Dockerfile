# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt requirements.txt

# 安装依赖
RUN pip install -r requirements.txt

# 复制当前目录中的文件到工作目录中
COPY . .

#默认模型
ENV MODEL_NAME=neofung/bge-reranker-large-1k

# 下载模型
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; import os; model_name = os.environ.get('MODEL_NAME', 'neofung/bge-reranker-large-1k'); AutoTokenizer.from_pretrained(model_name); AutoModelForSequenceClassification.from_pretrained(model_name);"

# 暴露端口
EXPOSE 8000

# 设置启动命令
CMD ["python", "main.py"]