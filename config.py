"""
RAG 项目统一配置 — ingest.py 与 app.py 共用。
"""
import os
import re
from pathlib import Path

import torch

# ---------------------------------------------------------------------------
# 路径 & 目录
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "pdf_rag"

# ---------------------------------------------------------------------------
# 模型路径
# ---------------------------------------------------------------------------
EMBED_MODEL = str(BASE_DIR / "models")                # bge-m3 (本地 PyTorch)
RERANK_MODEL = str(BASE_DIR / "models" / "reranker")  # bge-reranker-v2-m3 (本地)

# ---------------------------------------------------------------------------
# 设备 & HF 镜像
# ---------------------------------------------------------------------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# ---------------------------------------------------------------------------
# 分块参数（ingest.py 用）
# ---------------------------------------------------------------------------
CHUNK_MIN_CHARS = 300   # 最小 chunk，太小的段落不拆分
CHUNK_MAX_CHARS = 800   # 超过此值后拆分
OVERLAP_CHARS = 80      # 相邻 chunk 重叠字符数

# ---------------------------------------------------------------------------
# 标题检测正则（中文编号 + 常见章节格式）
# ---------------------------------------------------------------------------
HEADING_PATTERNS = [
    re.compile(r"^第[一二三四五六七八九十百千\d]+章"),
    re.compile(r"^第[一二三四五六七八九十百千\d]+节"),
    re.compile(r"^[一二三四五六七八九十]+[、．.]"),
    re.compile(r"^\d+[\.．、]\s"),
    re.compile(r"^[（(]\d+[)）]"),
    re.compile(r"^[A-Z][\.．、]\s"),
]

# ---------------------------------------------------------------------------
# 检索 / 重排参数（app.py 用）
# ---------------------------------------------------------------------------
RETRIEVAL_TOP_K = 20
RERANK_TOP_K = 5

# ---------------------------------------------------------------------------
# API 配置 — 密钥从环境变量或 .env 文件读取，代码中不保存任何密钥
# ---------------------------------------------------------------------------
def _load_env_file():
    """加载项目根目录下的 .env（若存在），不覆盖已有的环境变量。"""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file()

API_BASE = os.environ.get(
    "API_BASE", "https://aiagent.lakala.com/model-gateway/v1"
)
API_KEY = os.environ.get("API_KEY", "")
MODEL = os.environ.get("MODEL", "LKL-GLM-5.2-FP8")

# ---------------------------------------------------------------------------
# Prompt 模板（app.py 用）
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """你是一个基于内部文档回答问题的助手。请严格根据以下参考资料回答问题。
如果资料不足以回答，请明确说明"参考资料中未找到相关信息"。

在回答中引用资料时，使用 [1][2] 标记出处（对应下面参考资料的编号）。
用中文回答。请保持自然对话风格，像人类助手一样回答问题，不要只返回检索摘要。"""

USER_PROMPT_TEMPLATE = """参考资料：
{references}

对话历史：
{history}

问题：{question}"""