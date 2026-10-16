"""
前端展示配置 — Gradio 界面样式与文案，与后端逻辑（config.py）分离。

只放界面相关内容：主题、CSS、HTML 片段、文案、服务监听地址。
不放任何 API 密钥、模型路径、检索参数。
"""
import os

# ---------------------------------------------------------------------------
# 服务监听
# ---------------------------------------------------------------------------
SERVER_HOST = os.environ.get("RAG_SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("RAG_SERVER_PORT", "7860"))

# ---------------------------------------------------------------------------
# 页面文案
# ---------------------------------------------------------------------------
PAGE_TITLE = "内部文档 RAG 问答"
CHATBOT_HEIGHT = 580
TEXTBOX_PLACEHOLDER = "输入问题，回车发送…"
SEND_BTN_LABEL = "发送"
CLEAR_BTN_LABEL = "清空对话"
NO_REFS_MESSAGE = "**未找到相关参考资料**。请确认已入库相关文档。"
PANEL_TITLE = "来源追溯"

HEAD_HTML = """
<meta name='viewport' content='width=device-width, initial-scale=1'>
<script>
// 强制浅色模式：本界面按 Azure 浅色主题设计，
// 拦截 prefers-color-scheme 查询，防止 Gradio 跟随系统切换暗色
(function () {
    var orig = window.matchMedia.bind(window);
    window.matchMedia = function (q) {
        if (/prefers-color-scheme/.test(q)) {
            return {
                matches: false, media: q, onchange: null,
                addListener: function () {}, removeListener: function () {},
                addEventListener: function () {}, removeEventListener: function () {},
                dispatchEvent: function () { return false; }
            };
        }
        return orig(q);
    };
})();
</script>
"""

HEADER_HTML = """
<div class="az-header">
    <div class="az-logo">RAG</div>
    <div class="az-header-text">
        <h2>内部文档智能问答</h2>
        <p>本地检索增强生成 · 全链路离线 · 答案可溯源</p>
    </div>
    <div class="az-header-badge">bge-m3 · bge-reranker-v2-m3 · ChromaDB</div>
</div>
"""

FOOTER_HTML = """
<div class="az-footer">
    内部文档 RAG 问答 · 答案由本地大模型生成，引用来源见右侧面板
</div>
"""

# ---------------------------------------------------------------------------
# 来源追溯面板（右侧）— agent think 风格折叠卡片
# ---------------------------------------------------------------------------
SOURCES_EMPTY_HTML = """
<div class="src-panel-title">
    <span class="src-icon">&#9672;</span> 来源追溯
</div>
<div class="src-empty">
    <div class="src-empty-icon">&#128269;</div>
    提问后，这里会显示答案引用的文档来源<br>点击卡片可展开查看原文片段
</div>
"""

SOURCES_PANEL_TEMPLATE = """
<div class="src-panel-title">
    <span class="src-icon">&#9672;</span> 来源追溯
    <span class="src-count">{count} 条引用</span>
</div>
<div class="src-list">{cards}</div>
"""

SOURCE_CARD_TEMPLATE = """
<details class="src-card">
    <summary>
        <span class="src-idx">{index}</span>
        <span class="src-name" title="{filename}">{filename}</span>
        <span class="src-badge">P{page} &middot; {score}</span>
    </summary>
    <div class="src-body">{snippet}</div>
</details>
"""

# ---------------------------------------------------------------------------
# 页面样式 — Microsoft Azure Portal 风格
# 选择器同时兼容 Gradio 5 / 6 的 Chatbot DOM 结构
# ---------------------------------------------------------------------------
CSS = """
.gradio-container {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif !important;
    background: #F3F2F1 !important;
    max-width: 1440px !important;
    width: 96% !important;
    margin: 0 auto !important;
}

/* ===== Azure 顶部栏 ===== */
.az-header {
    display: flex;
    align-items: center;
    gap: 14px;
    background: linear-gradient(90deg, #005A9E 0%, #0078D4 55%, #2B88D8 100%);
    border-radius: 8px;
    padding: 16px 22px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(0,90,158,0.25);
}
.az-logo {
    width: 42px; height: 42px;
    background: rgba(255,255,255,0.16);
    border: 1px solid rgba(255,255,255,0.35);
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    color: #FFF; font-weight: 700; font-size: 0.78rem; letter-spacing: 0.5px;
}
.az-header-text { flex: 1; }
.az-header-text h2 {
    font-size: 1.2rem; font-weight: 600; color: #FFF; margin: 0;
}
.az-header-text p {
    font-size: 0.78rem; color: rgba(255,255,255,0.82); margin: 3px 0 0;
}
.az-header-badge {
    font-size: 0.7rem; color: rgba(255,255,255,0.9);
    background: rgba(0,0,0,0.18);
    border: 1px solid rgba(255,255,255,0.25);
    padding: 5px 12px; border-radius: 20px;
    white-space: nowrap;
}

/* ===== 主布局 ===== */
.main-row { gap: 16px !important; align-items: stretch !important; }

/* ===== 聊天区 ===== */
.chatbot {
    border-radius: 8px !important;
    border: 1px solid #EDEBE9 !important;
    background: #FFFFFF !important;
    box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.07), 0 0.3px 0.9px rgba(0,0,0,0.05) !important;
}

/* 用户气泡 */
.chatbot .user,
.user-row .user.message,
.bubble.user-row .user {
    background: #0078D4 !important;
    color: #FFF !important;
    border-radius: 4px 12px 12px 12px !important;
    padding: 10px 16px !important;
    font-size: 0.9rem !important;
    box-shadow: 0 2px 6px rgba(0,120,212,0.22) !important;
}

/* 机器人气泡 */
.chatbot .bot,
.bot-row .bot.message,
.bubble.bot-row .bot {
    background: #FFFFFF !important;
    color: #201F1E !important;
    border-radius: 12px 4px 12px 12px !important;
    padding: 12px 18px !important;
    font-size: 0.88rem !important;
    line-height: 1.65 !important;
    border: 1px solid #EDEBE9 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04) !important;
}

/* ===== 输入区 ===== */
.input-row {
    border: 1px solid #D2D0CE !important;
    border-radius: 6px !important;
    background: #FFFFFF !important;
    box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.07) !important;
    padding: 6px 8px 6px 16px !important;
    margin-top: 12px !important;
}
.input-row:focus-within {
    border-color: #0078D4 !important;
    box-shadow: 0 0 0 2px rgba(0,120,212,0.18) !important;
}
.input-row textarea {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    font-size: 0.92rem !important;
    resize: none !important;
    min-height: 42px !important;
    padding: 10px 0 !important;
    background: transparent !important;
}

/* ===== 来源追溯面板（右侧）===== */
.src-panel {
    background: #FFFFFF !important;
    border: 1px solid #EDEBE9 !important;
    border-radius: 8px !important;
    box-shadow: 0 1.6px 3.6px rgba(0,0,0,0.07), 0 0.3px 0.9px rgba(0,0,0,0.05) !important;
    padding: 16px 18px !important;
    height: 100%;
}
.src-panel-title {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.92rem; font-weight: 600; color: #323130;
    border-bottom: 2px solid #0078D4;
    padding-bottom: 10px; margin-bottom: 12px;
}
.src-icon { color: #0078D4; font-size: 0.9rem; }
.src-count {
    margin-left: auto;
    font-size: 0.7rem; font-weight: 600; color: #0078D4;
    background: #EFF6FC; border: 1px solid #C7E0F4;
    padding: 2px 10px; border-radius: 12px;
}
.src-empty {
    text-align: center;
    color: #8A8886; font-size: 0.82rem; line-height: 1.8;
    padding: 48px 12px;
}
.src-empty-icon { font-size: 1.6rem; margin-bottom: 10px; opacity: 0.5; }

/* 折叠卡片 — agent think 风格 */
.src-list { display: flex; flex-direction: column; gap: 8px; }
.src-card {
    border: 1px solid #EDEBE9;
    border-radius: 6px;
    background: #FAF9F8;
    overflow: hidden;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}
.src-card:hover { border-color: #C7E0F4; }
.src-card[open] {
    border-color: #0078D4;
    box-shadow: 0 1px 4px rgba(0,120,212,0.12);
    background: #FFFFFF;
}
.src-card summary {
    list-style: none;
    cursor: pointer;
    display: flex; align-items: center; gap: 8px;
    padding: 10px 12px;
    user-select: none;
}
.src-card summary::-webkit-details-marker { display: none; }
.src-card summary::before {
    content: "\\25B8";
    color: #0078D4;
    font-size: 0.75rem;
    transition: transform 0.18s ease;
    flex-shrink: 0;
}
.src-card[open] summary::before { transform: rotate(90deg); }
.src-idx {
    flex-shrink: 0;
    width: 20px; height: 20px;
    background: #0078D4; color: #FFF;
    border-radius: 4px;
    font-size: 0.68rem; font-weight: 600;
    display: inline-flex; align-items: center; justify-content: center;
}
.src-name {
    flex: 1; min-width: 0;
    font-size: 0.8rem; font-weight: 600; color: #323130;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.src-badge {
    flex-shrink: 0;
    font-size: 0.66rem; color: #605E5C;
    background: #F3F2F1; border: 1px solid #EDEBE9;
    padding: 2px 8px; border-radius: 10px;
    white-space: nowrap;
}
.src-card[open] .src-badge { background: #EFF6FC; border-color: #C7E0F4; color: #0078D4; }
.src-body {
    padding: 10px 14px 14px 40px;
    font-size: 0.78rem; color: #605E5C; line-height: 1.6;
    border-top: 1px dashed #EDEBE9;
    word-break: break-word;
}

/* ===== 页脚 ===== */
.az-footer {
    text-align: center;
    padding: 14px 0 4px;
    font-size: 0.72rem;
    color: #A19F9D;
}

/* ===== 暗色模式兜底 =====
   即使 head 脚本未生效（如缓存的旧页面），
   也把 Gradio 暗色变量强制改回浅色值，保证配色一致 */
.dark, .dark .gradio-container {
    --body-background-fill: #F3F2F1 !important;
    --background-fill-primary: #FFFFFF !important;
    --background-fill-secondary: #FAF9F8 !important;
    --background-fill-tertiary: #F3F2F1 !important;
    --body-text-color: #201F1E !important;
    --body-text-color-subdued: #605E5C !important;
    --block-background-fill: #FFFFFF !important;
    --block-border-color: #EDEBE9 !important;
    --block-title-text-color: #323130 !important;
    --block-label-text-color: #323130 !important;
    --border-color-primary: #EDEBE9 !important;
    --border-color-accent: #0078D4 !important;
    --border-color-accent-subdued: #C7E0F4 !important;
    --color-accent-soft: #EFF6FC !important;
    --input-background-fill: #FFFFFF !important;
    --button-secondary-background-fill: #FFFFFF !important;
    --button-secondary-text-color: #323130 !important;
    --shadow-drop: 0 1px 2px rgba(0,0,0,0.06) !important;
    --shadow-drop-lg: 0 1.6px 3.6px rgba(0,0,0,0.07) !important;
    --chatbot-code-background-color: #F3F2F1 !important;
    color-scheme: light !important;
}
.dark .gradio-container { background: #F3F2F1 !important; }

/* 聊天气泡内文本颜色兜底（暗色变量失效时也能读清） */
.chatbot .bot, .chatbot .bot .prose, .chatbot .bot p,
.chatbot .bot li, .chatbot .bot span {
    color: #201F1E !important;
}
.chatbot .user, .chatbot .user .prose, .chatbot .user p,
.chatbot .user span {
    color: #FFFFFF !important;
}

/* 隐藏头像占位与消息内装饰性分隔元素（消除气泡内竖线） */
.chatbot .avatar-container { display: none !important; }
"""
