import os
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional

app = FastAPI()

# 加载模型和分词器
model_name = os.environ.get('MODEL_NAME', 'neofung/bge-reranker-large-1k')
# 设置服务监听ip
host = os.environ.get('HOST', '0.0.0.0')
# 设置服务监听端口
port = int(os.environ.get('PORT', 8000))
# 设置服务进程数量
workers = int(os.environ.get('WORKERS', 1))

# 模型全局变量
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# 如果有GPU可用，使用GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)


class Query(BaseModel):
    model: str
    query: str
    top_n: Optional[int] = None
    documents: list


@app.post("/v1/rerank")
async def rerank(query: Query):
    try:
        if query.model != model_name:
            raise Exception('暂不支持模型：' + query.model)

        # 对输入进行编码
        inputs = tokenizer(
            [query.query] * len(query.documents),
            query.documents,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(device)

        # 模型推理
        with torch.no_grad():
            outputs = model(**inputs)
            scores = outputs.logits.squeeze().tolist()

        # 创建包含索引和分数的列表
        indexed_scores = list(enumerate(scores))

        # 返回重排后的结果
        ranked_docs = sorted(indexed_scores, key=lambda x: x[1], reverse=True)

        # 如果设置了top_n且大于1，返回前top_n个结果，否则返回全部
        if query.top_n and query.top_n > 0:
            ranked_docs = ranked_docs[:query.top_n]

        # 格式化输出
        results = [{"index": idx, "relevance_score": score} for idx, score in ranked_docs]

        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=host, port=port, workers=workers)
