# 内部文档 RAG 问答系统

基于本地 PDF 资料库的智能问答系统——检索、重排、生成全链路均在本地完成，**不联网**，适用于企业内部文档的私密问答场景。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| 向量模型 | **bge-m3** | BAAI 多语言向量模型，生成 1024 维 embedding |
| 重排模型 | **bge-reranker-v2-m3** | BAAI Cross-Encoder，对检索结果精排 |
| 向量库 | **ChromaDB** | 本地持久化向量数据库，余弦相似度检索 |
| 对话界面 | **Gradio 6** | Chatbot 风格 Web UI |
| 大模型 | **OpenAI** | 通过 OpenAI API 调用 |
| PDF 解析 | **PyMuPDF** | 逐页提取文本 |

## 项目结构

```
rag/
├── app.py                 # Gradio Web 服务入口（检索 + 重排 + LLM 生成）
├── ingest.py              # 离线入库脚本（PDF → 分块 → 向量化 → ChromaDB）
├── config.py              # 后端配置（路径、模型、分块参数、Prompt）
├── frontend_config.py     # 前端配置（Azure 样式、文案、来源面板模板、端口）
├── verify_rag.py          # 端到端验收脚本（通过 Gradio API 发送真实问答）
├── requirements.txt       # Python 依赖清单
├── .env                   # 密钥配置（API_KEY 等，已加入 .gitignore，不提交）
├── .env.example           # 密钥配置模板（可复制为 .env 后填写）
├── docs/                  # 待入库的 PDF 文档目录
│   └── attention_is_all_you_need.pdf
├── models/                # 本地模型文件
│   ├── ...                #   bge-m3（PyTorch 格式）
│   └── reranker/          #   bge-reranker-v2-m3
├── chroma_db/             # ChromaDB 持久化数据（自动生成）
└── README.md
```

界面为 **Microsoft Azure 风格**：左侧对话区，右侧「来源追溯」面板——每条引用是一张可折叠卡片（编号 + 文件名 + 页码/相关度徽章），点击展开查看原文片段。

## 安装依赖

使用腾讯 PyPI 镜像加速安装：

```bash
pip install -r requirements.txt -i https://mirrors.cloud.tencent.com/pypi/simple
```

> 依赖清单：`torch>=2.6`、`chromadb`、`pymupdf`、`sentence-transformers`、`gradio>=6.0`、`FlagEmbedding`、`openai`

## 模型下载

从 ModelScope 下载所需的两个模型，放入 `models/` 目录：

```bash
# bge-m3 向量模型
git lfs install
git clone https://www.modelscope.cn/BAAI/bge-m3.git models/

# bge-reranker-v2-m3 重排模型
git clone https://www.modelscope.cn/BAAI/bge-reranker-v2-m3.git models/reranker/
```

> 模型目录结构需满足：`models/` 下直接放 bge-m3 的权重与配置，`models/reranker/` 下放 reranker 的权重与配置。

## 入库

将 PDF 文档放入 `docs/` 目录，然后运行：

```bash
# 扫描 docs/ 下所有 PDF，全量入库（已存在的 chunk 自动跳过）
python ingest.py

# 清空旧数据后重建
python ingest.py --reset

# 增量添加指定文件
python ingest.py docs/某文档.pdf
```

入库流程：**PDF 文本提取 → 标题感知分块（300–800 字符，80 字符重叠）→ bge-m3 向量化 → 写入 ChromaDB**。

## 启动

```bash
python app.py
```

浏览器打开 **http://localhost:7860** 即可使用。

首次启动会加载向量模型与重排模型，耗时较长，请耐心等待。启动后模型常驻内存，后续问答响应迅速。

如需更换监听地址或端口（如 7860 被占用）：

```bash
# Windows
set RAG_SERVER_PORT=7861 && python app.py

# Linux / macOS
RAG_SERVER_PORT=7861 python app.py
```

## 配置说明

配置按职责分离为三个文件：

- **`config.py`** — 后端配置：路径、模型、分块参数、检索参数、Prompt 模板
- **`frontend_config.py`** — 前端配置：Azure 样式 CSS、页面文案、来源面板 HTML 模板、服务监听地址
- **`.env`** — 密钥配置（已加入 `.gitignore`，不会被提交；可复制 `.env.example` 生成）

### LLM API

密钥从**环境变量或 `.env` 文件**读取（环境变量优先），代码中不保存任何明文密钥：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `API_BASE` | `https://api.openai.com/v1` | API 网关地址 |
| `API_KEY` | 无（必须配置） | API 密钥 |
| `MODEL` | `OpenAI` | 模型名称 |

设置方式（任选其一）：

```bash
# 方式一：写入 .env 文件（推荐，参考 .env.example）
API_KEY=your-key-here

# 方式二：环境变量
set API_KEY=your-key-here        # Windows
export API_KEY=your-key-here     # Linux / macOS
```

未配置密钥时应用照常启动，仅在调用 LLM 时提示失败。

### 检索参数（`config.py` 第 52–53 行）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `RETRIEVAL_TOP_K` | 20 | 向量检索返回数量 |
| `RERANK_TOP_K` | 5 | 重排后保留数量 |

### 分块参数（`config.py` 第 33–35 行）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `CHUNK_MIN_CHARS` | 300 | 最小 chunk 字符数，低于此不拆分 |
| `CHUNK_MAX_CHARS` | 800 | 最大 chunk 字符数，超过时拆分 |
| `OVERLAP_CHARS` | 80 | 相邻 chunk 重叠字符数（约 10%） |

### 前端展示（`frontend_config.py`）

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `RAG_SERVER_HOST` | `127.0.0.1` | 监听地址 |
| `RAG_SERVER_PORT` | `7860` | 监听端口 |

页面样式（Azure 主题 CSS）、文案、来源面板模板均在 `frontend_config.py` 中，调整界面无需改动业务逻辑。

### 其他超参数

| 参数 | 默认值 | 位置 | 说明 |
|------|--------|------|------|
| `temperature` | 0.1 | `app.py:191` | LLM 生成温度 |
| `max_tokens` | 2048 | `app.py:192` | LLM 最大输出 token |
| `max_length` | 512 | `app.py:59` | CrossEncoder 输入截断 |
| embedding dim | 1024 | bge-m3 固定 | 向量维度 |
| similarity | cosine | `ingest.py:156` | ChromaDB HNSW 空间 |
| DEVICE | cuda / cpu | `config.py:27` | 自动检测 |

## 数据流

```
用户提问
  │
  ▼
┌──────────────┐    Top-20     ┌──────────────┐
│ bge-m3 向量化 │ ────────────► │ ChromaDB 检索 │
└──────────────┘               └──────┬───────┘
                                      │ 粗排结果
                                      ▼
                              ┌──────────────────┐
                              │ bge-reranker 重排 │
                              └────────┬─────────┘
                                       │ Top-5 精排
                                       ▼
                              ┌──────────────────┐
                              │ OpenAI 生成  │
                              └────────┬─────────┘
                                       │
                                       ▼
                              答案 + 出处引用
```

1. 用户问题经 **bge-m3** 编码为向量
2. **ChromaDB** 余弦相似度检索 Top-20 候选段落
3. **bge-reranker-v2-m3** 对候选段落精排，取 Top-5
4. 将精排段落作为参考资料，组装 Prompt 调用 **OpenAI** 生成最终答案
5. 答案正文中以 `[1][2]` 标记出处；引用来源（文件名、页码、相关度、原文片段）展示在右侧「来源追溯」面板，可折叠展开

## 验收测试

启动服务后，运行冒烟 + 单元测试：

```bash
python -c "
import sys; passed=0; failed=0
def t(n,f):
    global passed,failed
    try: f(); passed+=1; print(f'✅ {n}')
    except Exception as e: failed+=1; print(f'❌ {n}: {e}')

def t_config():
    from config import EMBED_MODEL,RERANK_MODEL,DEVICE,RETRIEVAL_TOP_K,RERANK_TOP_K,MODEL
    from pathlib import Path
    assert Path(EMBED_MODEL).exists()
    assert Path(RERANK_MODEL).exists()
    assert RETRIEVAL_TOP_K==20 and RERANK_TOP_K==5
    assert MODEL

def t_heading():
    from ingest import is_heading
    assert is_heading('第一章 概述') and not is_heading('normal text')

def t_chunk():
    from ingest import chunk_text
    assert len(chunk_text('hello'))==1
    paras='.\\n\\n'.join(['word '*60]*10)
    assert len(chunk_text(paras))>=2

def t_chromadb():
    from app import get_collection
    assert get_collection().count()>0

def t_embed():
    from app import get_embed_model
    import numpy as np
    emb=get_embed_model().encode('test',normalize_embeddings=True)
    assert emb.shape[0]==1024 and isinstance(emb,np.ndarray)

def t_retrieve():
    from app import retrieve
    r=retrieve('Transformer')
    assert len(r)>=1 and r[0]['filename']=='attention_is_all_you_need.pdf'

def t_prompt():
    from app import build_prompt
    p=build_prompt('q',[{'filename':'f.pdf','page':1,'text':'t'}],[])
    assert '[1]' in p and 'f.pdf' in p

def t_clear():
    from app import chat_fn
    _,c,_=chat_fn('hi',[])
    assert c==''

def t_sources():
    from app import format_sources_html
    h=format_sources_html([{'text':'片段','filename':'f.pdf','page':1,'score':0.9}])
    assert 'src-card' in h and 'f.pdf' in h

for name,fn in [('config',t_config),('heading',t_heading),('chunk',t_chunk),
    ('chromadb',t_chromadb),('embed',t_embed),('retrieve',t_retrieve),
    ('prompt',t_prompt),('clear',t_clear),('sources',t_sources)]:
    t(name,fn)
print(f'\\n{passed}/{(passed+failed)} passed')
sys.exit(0 if failed==0 else 1)
"
```

### 典型测试结果

```
✅ config   ✅ heading   ✅ chunk    ✅ chromadb   ✅ embed
✅ retrieve ✅ prompt    ✅ clear    ✅ sources
9/9 passed
```

## 硬件要求

- **GPU**：推荐 NVIDIA GPU（bge-m3 ~2GB 显存，reranker ~2GB 显存，共约 4GB）
- **CPU**：自动回退，但向量化与重排速度较慢
- **磁盘**：模型文件约 4GB，ChromaDB 视文档量而定