"""
Gradio 问答 Web 服务 — 本地 RAG 系统。

启动前设置环境变量:
    set API_BASE=http://your-api/v1
    set API_KEY=your-key
    set MODEL=LKL-GLM-5.2-FP8     (可选，默认值)

用法:
    python app.py
    浏览器打开 http://localhost:7860
"""

import chromadb
import gradio as gr
from gradio.themes import Soft
from openai import OpenAI
from sentence_transformers import CrossEncoder, SentenceTransformer

from config import (
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBED_MODEL,
    RERANK_MODEL,
    DEVICE,
    RETRIEVAL_TOP_K,
    RERANK_TOP_K,
    API_BASE,
    API_KEY,
    MODEL,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)

# ---------------------------------------------------------------------------
# 初始化（延迟加载）
# ---------------------------------------------------------------------------
_embed_model = None
_rerank_model = None
_chroma_client = None
_collection = None
_llm_client = None


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        print(f"加载向量模型: {EMBED_MODEL}")
        _embed_model = SentenceTransformer(EMBED_MODEL, device=DEVICE)
    return _embed_model


def get_rerank_model():
    global _rerank_model
    if _rerank_model is None:
        print(f"加载重排模型: {RERANK_MODEL}")
        _rerank_model = CrossEncoder(
            RERANK_MODEL,
            max_length=512,
            device=DEVICE,
        )
    return _rerank_model


def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        try:
            _collection = _chroma_client.get_collection(COLLECTION_NAME)
            print(f"ChromaDB collection 已连接，共 {_collection.count()} 条记录")
        except Exception:
            raise RuntimeError(
                f"未找到 ChromaDB collection '{COLLECTION_NAME}'。"
                f"请先运行 python ingest.py 入库 PDF 文档。"
            )
    return _collection


def get_llm_client():
    global _llm_client
    if _llm_client is None:
        if not API_BASE or not API_KEY:
            print("警告: API_BASE / API_KEY 未设置，LLM 调用将失败")
        _llm_client = OpenAI(
            base_url=API_BASE,
            api_key=API_KEY,
        )
    return _llm_client


# ---------------------------------------------------------------------------
# RAG 核心流程
# ---------------------------------------------------------------------------


def retrieve(query: str):
    """检索 + 重排，返回 top-K 相关 chunk 列表。"""
    embed_model = get_embed_model()
    collection = get_collection()

    # 1. bge-m3 向量化查询
    q_embedding = embed_model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    # 2. ChromaDB 检索 top-20
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=RETRIEVAL_TOP_K,
        include=["documents", "metadatas", "distances"],
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    docs = results["documents"][0]
    metas_raw = results["metadatas"]
    metas = metas_raw[0] if metas_raw else [{} for _ in docs]

    # 3. bge-reranker-v2-m3 重排取 top-5
    if len(docs) > RERANK_TOP_K:
        rerank_model = get_rerank_model()
        pairs = [[query, doc] for doc in docs]
        scores = rerank_model.predict(pairs)

        # 按分数降序排列
        ranked = sorted(
            zip(docs, metas, scores),
            key=lambda x: x[2],
            reverse=True,
        )
        ranked = ranked[:RERANK_TOP_K]
    else:
        ranked = [(d, m, 0.0) for d, m in zip(docs, metas)]

    return [
        {
            "text": doc,
            "filename": meta.get("filename", "?"),
            "page": meta.get("page", "?"),
            "score": float(score),
        }
        for doc, meta, score in ranked
    ]


def build_prompt(query: str, refs: list[dict], history: list) -> str:
    """构建发给 LLM 的完整 prompt。"""
    ref_lines = []
    for i, ref in enumerate(refs, 1):
        ref_lines.append(
            f"[{i}] (来源: {ref['filename']}, 第{ref['page']}页)\n"
            f"{ref['text']}\n"
        )
    references_text = "\n".join(ref_lines)

    # 最近 4 轮对话历史
    history_text = ""
    for h in history[-4:]:
        if isinstance(h, dict):
            role = "用户" if h["role"] == "user" else "助手"
            content = h.get("content", "")
            # 截断长回复
            if len(content) > 300:
                content = content[:300] + "..."
            history_text += f"{role}: {content}\n"

    return USER_PROMPT_TEMPLATE.format(
        references=references_text,
        history=history_text or "（无历史）",
        question=query,
    )


def call_llm(query: str, refs: list[dict], history: list | None = None) -> str:
    """调用 API 生成答案。"""
    if history is None:
        history = []
    client = get_llm_client()
    user_prompt = build_prompt(query, refs, history)

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        return response.choices[0].message.content or "**LLM 返回了空内容**"
    except Exception as e:
        return f"**LLM 调用失败**: {e}"


# ---------------------------------------------------------------------------
# Gradio 界面 — 样式与文案见 frontend_config.py
# ---------------------------------------------------------------------------
import html as _html

from frontend_config import (
    CSS,
    HEAD_HTML,
    HEADER_HTML,
    FOOTER_HTML,
    PAGE_TITLE,
    TEXTBOX_PLACEHOLDER,
    SEND_BTN_LABEL,
    CLEAR_BTN_LABEL,
    NO_REFS_MESSAGE,
    SOURCES_EMPTY_HTML,
    SOURCES_PANEL_TEMPLATE,
    SOURCE_CARD_TEMPLATE,
    SERVER_HOST,
    SERVER_PORT,
)


def format_sources_html(refs: list[dict]) -> str:
    """将检索结果渲染为右侧面板的折叠卡片 HTML（agent think 风格）。"""
    if not refs:
        return SOURCES_EMPTY_HTML
    cards = []
    for i, ref in enumerate(refs, 1):
        snippet = ref["text"][:400] + ("..." if len(ref["text"]) > 400 else "")
        cards.append(SOURCE_CARD_TEMPLATE.format(
            index=i,
            filename=_html.escape(str(ref["filename"])),
            page=_html.escape(str(ref["page"])),
            score=f"{ref['score']:.4f}",
            snippet=_html.escape(snippet),
        ))
    return SOURCES_PANEL_TEMPLATE.format(count=len(refs), cards="".join(cards))


def chat_fn(message: str, history: list):
    """Gradio Chatbot 回调：返回答案，来源展示在右侧面板。"""
    if not message or not message.strip():
        return history, message, gr.skip()

    # 1. 检索
    refs = retrieve(message.strip())
    if not refs:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": NO_REFS_MESSAGE})
        return history, "", SOURCES_EMPTY_HTML

    # 2. 生成
    answer = call_llm(message, refs, history)

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})
    return history, "", format_sources_html(refs)


def build_ui():
    """构建 Gradio 界面。"""
    with gr.Blocks(
        title=PAGE_TITLE,
        fill_height=True,
    ) as demo:
        # 顶部导航栏：品牌 + 新对话按钮
        with gr.Row(elem_classes=["topbar"]):
            gr.HTML(HEADER_HTML)
            clear_btn = gr.Button(
                CLEAR_BTN_LABEL,
                variant="secondary",
                size="sm",
                scale=0,
                min_width=88,
                elem_classes=["new-chat-btn"],
            )

        with gr.Row(elem_classes=["main-row"]):
            # 左侧：对话区（消息流 + 底部固定输入区）
            with gr.Column(scale=1, elem_classes=["chat-column"]):
                chatbot = gr.Chatbot(
                    label="",
                    scale=1,
                    show_label=False,
                    elem_classes=["chatbot"],
                )

                with gr.Column(elem_classes=["composer"]):
                    with gr.Row(elem_classes=["input-row"]):
                        msg = gr.Textbox(
                            placeholder=TEXTBOX_PLACEHOLDER,
                            scale=7,
                            show_label=False,
                            container=False,
                        )
                        send_btn = gr.Button(
                            SEND_BTN_LABEL,
                            variant="primary",
                            scale=1,
                            min_width=72,
                        )
                    gr.HTML(FOOTER_HTML)

            # 右侧：来源追溯面板（独立滚动）
            with gr.Column(scale=0, min_width=320, elem_classes=["src-column"]):
                sources_panel = gr.HTML(
                    value=SOURCES_EMPTY_HTML,
                    elem_classes=["src-panel"],
                )

        # 事件绑定
        chat_inputs = [msg, chatbot]
        chat_outputs = [chatbot, msg, sources_panel]
        msg.submit(fn=chat_fn, inputs=chat_inputs, outputs=chat_outputs)
        send_btn.click(fn=chat_fn, inputs=chat_inputs, outputs=chat_outputs)
        clear_btn.click(
            fn=lambda: (None, [], SOURCES_EMPTY_HTML),
            inputs=[],
            outputs=[msg, chatbot, sources_panel],
            queue=False,
        )

    return demo


if __name__ == "__main__":
    # 启动时预热模型
    print("正在加载模型（首次启动较慢，请耐心等待）...")
    _embed_model = get_embed_model()
    _rerank_model = get_rerank_model()
    get_collection()
    # CUDA 推理预热 —— 避免首问卡顿
    print("预热 CUDA 推理引擎...")
    _embed_model.encode("预热", normalize_embeddings=True)
    _rerank_model.predict([["预热", "预热文档"]])
    print("所有模型加载完毕，启动 Web 服务...")

    demo = build_ui()
    demo.launch(
        server_name=SERVER_HOST,
        server_port=SERVER_PORT,
        inbrowser=False,
        theme=Soft(primary_hue="blue"),
        css=CSS,
        head=HEAD_HTML,
    )
