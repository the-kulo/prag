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
PAGE_TITLE = "内部文档智能问答"
TEXTBOX_PLACEHOLDER = "输入问题，回车发送…"
SEND_BTN_LABEL = "发送"
CLEAR_BTN_LABEL = "新对话"
NO_REFS_MESSAGE = "**未找到相关参考资料**。请确认已入库相关文档。"
PANEL_TITLE = "来源追溯"

HEAD_HTML = """
<meta name='viewport' content='width=device-width, initial-scale=1'>
<script>
// 强制浅色模式：拦截 prefers-color-scheme 查询，防止 Gradio 跟随系统切换暗色
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
<div class="brand">
    <div class="brand-logo">R</div>
    <div class="brand-text">
        <h1>内部文档智能问答</h1>
        <p>检索增强生成 · 答案可溯源</p>
    </div>
</div>
"""

FOOTER_HTML = """
<div class="footnote">内容由 AI 生成，仅供参考 · 引用来源见右侧面板</div>
"""

# ---------------------------------------------------------------------------
# 来源追溯面板（右侧）— 折叠卡片
# ---------------------------------------------------------------------------
SOURCES_EMPTY_HTML = """
<div class="src-panel-title">来源追溯</div>
<div class="src-empty">
    提问后，这里会显示答案引用的文档来源<br>点击卡片可展开查看原文片段
</div>
"""

SOURCES_PANEL_TEMPLATE = """
<div class="src-panel-title">
    来源追溯
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
# 页面样式 — Kimi / DeepSeek 风格
# 顶部导航 + 居中对话 + 底部固定输入框 + 右侧独立滚动来源栏
# 选择器兼容 Gradio 5 / 6 的 Chatbot DOM 结构
# ---------------------------------------------------------------------------
CSS = """
:root {
    --brand: #2563EB;
    --page-bg: #F6F7F9;
    --line: #E5E8EE;
    --text-main: #1F2937;
    --text-muted: #8A94A6;
}

html, body { background: var(--page-bg) !important; }

.gradio-container {
    font-family: 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif !important;
    background: var(--page-bg) !important;
    max-width: 100% !important;
    width: 100% !important;
    height: 100vh !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
}
/* 清除 Gradio 默认内容宽度和页面留白，让导航栏铺满 */
.gradio-container > .main,
.gradio-container > .main > .wrap,
.gradio-container > .main > .wrap > .contain {
    max-width: none !important;
    width: 100% !important;
    padding: 0 !important;
}
.gradio-container footer { display: none !important; }

/* ===== 顶部导航栏 ===== */
.topbar {
    height: 60px !important;
    min-height: 60px !important;
    max-height: 60px !important;
    flex: 0 0 auto !important;
    background: #FFFFFF !important;
    border-bottom: 1px solid var(--line) !important;
    padding: 0 20px !important;
    gap: 12px !important;
    align-items: center !important;
}
.topbar > .block,
.topbar > .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
.brand { display: flex; align-items: center; gap: 12px; }
.brand-logo {
    width: 34px; height: 34px; border-radius: 10px;
    background: linear-gradient(135deg, #2563EB, #4F8CFF);
    color: #FFF; font-weight: 700; font-size: 1.05rem;
    display: flex; align-items: center; justify-content: center;
}
.brand-text h1 {
    font-size: 1rem; font-weight: 600; color: var(--text-main); margin: 0;
}
.brand-text p { font-size: 0.72rem; color: var(--text-muted); margin: 2px 0 0; }
.new-chat-btn { flex: 0 0 auto !important; }
.topbar button {
    border-radius: 8px !important;
    border: 1px solid var(--line) !important;
    color: #4B5563 !important;
    background: #FFFFFF !important;
}
.topbar button:hover { border-color: var(--brand) !important; color: var(--brand) !important; }

/* ===== 主区域：左对话 + 右来源，高度锁定为视口减导航 ===== */
.main-row {
    height: calc(100vh - 60px) !important;
    min-height: 0 !important;
    flex: 1 1 0 !important;
    gap: 0 !important;
    align-items: stretch !important;
    overflow: hidden !important;
}
.chat-column {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 0 !important;
    min-width: 0 !important;
    min-height: 0 !important;
    overflow: hidden !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}
.chat-column > .block,
.chat-column > .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
/* 对话滚动区：占据输入框之外的全部高度 */
.chat-column > .block:has(.chatbot) {
    flex: 1 1 0 !important;
    min-height: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
}
.chatbot {
    flex: 1 1 0 !important;
    min-height: 0 !important;
    height: 100% !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* 消息流：内容居中，类似 Kimi / DeepSeek 的单列阅读宽度 */
.chatbot .message-row {
    width: 100% !important;
    max-width: 840px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}
.chatbot .avatar-container { display: none !important; }

/* 用户消息：右侧浅蓝灰气泡，宽度随内容 */
.chatbot .user,
.user-row .user.message,
.bubble.user-row .user {
    background: #E9F1FC !important;
    color: var(--text-main) !important;
    border: none !important;
    border-radius: 16px !important;
    padding: 10px 16px !important;
    font-size: 0.94rem !important;
    line-height: 1.6 !important;
    box-shadow: none !important;
    width: fit-content !important;
    max-width: 78% !important;
    flex: 0 1 auto !important;
}
.chatbot .user, .chatbot .user .prose, .chatbot .user p,
.chatbot .user span { color: var(--text-main) !important; }

/* 隐藏顶部冗余工具条；单条消息的复制按钮仅悬停时出现 */
.chatbot .top-panel { display: none !important; }
.chatbot .message-buttons {
    opacity: 0;
    transition: opacity 0.15s ease;
}
.chatbot .message-row:hover .message-buttons { opacity: 1; }
.chatbot .message-buttons .icon-button-wrapper {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* AI 消息：无气泡，直接排版 */
.chatbot .bot,
.bot-row .bot.message,
.bubble.bot-row .bot {
    background: transparent !important;
    color: var(--text-main) !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 4px 0 !important;
    font-size: 0.94rem !important;
    line-height: 1.75 !important;
    box-shadow: none !important;
    max-width: 100% !important;
}
.chatbot .bot, .chatbot .bot .prose, .chatbot .bot p,
.chatbot .bot li, .chatbot .bot span { color: var(--text-main) !important; }

/* ===== 底部输入区：固定不随对话滚动 ===== */
.composer {
    flex: 0 0 auto !important;
    width: 100% !important;
    max-width: 888px !important;
    margin: 0 auto !important;
    padding: 8px 24px 12px !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.composer > .block,
.composer > .form {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.input-row {
    background: #FFFFFF !important;
    border: 1px solid var(--line) !important;
    border-radius: 14px !important;
    padding: 6px 6px 6px 16px !important;
    margin: 0 !important;
    box-shadow: 0 2px 10px rgba(15, 23, 42, 0.05) !important;
}
.input-row:focus-within {
    border-color: #93B4F5 !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}
.input-row textarea {
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
    background: transparent !important;
    font-size: 0.95rem !important;
    resize: none !important;
    min-height: 40px !important;
    padding: 10px 0 !important;
}
.input-row button {
    border-radius: 10px !important;
    min-height: 40px !important;
    background: var(--brand) !important;
}
.footnote {
    text-align: center;
    font-size: 0.72rem;
    color: #9AA3B2;
    margin-top: 8px;
}

/* ===== 右侧来源追溯栏：独立滚动，不影响对话区 ===== */
.src-column {
    display: flex !important;
    flex-direction: column !important;
    flex: 0 0 320px !important;
    width: 320px !important;
    max-width: 320px !important;
    min-height: 0 !important;
    overflow: hidden !important;
    background: #FFFFFF !important;
    border: none !important;
    border-left: 1px solid var(--line) !important;
    box-shadow: none !important;
    padding: 0 !important;
}
.src-column > .block {
    flex: 1 1 0 !important;
    min-height: 0 !important;
    display: flex !important;
    flex-direction: column !important;
    overflow: hidden !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
.src-panel {
    flex: 1 1 0 !important;
    height: 100% !important;
    min-height: 0 !important;
    overflow-y: auto !important;
    background: #FFFFFF !important;
    border: none !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    padding: 18px 16px !important;
}
.src-panel-title {
    display: flex; align-items: center; gap: 8px;
    font-size: 0.9rem; font-weight: 600; color: var(--text-main);
    padding-bottom: 12px; margin-bottom: 12px;
    border-bottom: 1px solid var(--line);
}
.src-count {
    margin-left: auto;
    font-size: 0.68rem; font-weight: 600; color: var(--brand);
    background: #EFF4FE; border: 1px solid #D8E5FB;
    padding: 2px 10px; border-radius: 12px;
}
.src-empty {
    text-align: center;
    color: var(--text-muted); font-size: 0.82rem; line-height: 1.8;
    padding: 48px 12px;
}

/* 折叠卡片 */
.src-list { display: flex; flex-direction: column; gap: 8px; }
.src-card {
    border: 1px solid var(--line);
    border-radius: 10px;
    background: #FAFBFC;
    overflow: hidden;
}
.src-card:hover { border-color: #C4D6F5; }
.src-card[open] { border-color: #93B4F5; background: #FFFFFF; }
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
    color: var(--brand);
    font-size: 0.75rem;
    transition: transform 0.18s ease;
    flex-shrink: 0;
}
.src-card[open] summary::before { transform: rotate(90deg); }
.src-idx {
    flex-shrink: 0;
    width: 20px; height: 20px;
    background: #E9F1FC; color: var(--brand);
    border-radius: 6px;
    font-size: 0.68rem; font-weight: 600;
    display: inline-flex; align-items: center; justify-content: center;
}
.src-name {
    flex: 1; min-width: 0;
    font-size: 0.8rem; font-weight: 600; color: var(--text-main);
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.src-badge {
    flex-shrink: 0;
    font-size: 0.66rem; color: #6B7280;
    background: #F3F4F6; border: 1px solid var(--line);
    padding: 2px 8px; border-radius: 10px;
    white-space: nowrap;
}
.src-body {
    padding: 10px 14px 14px 40px;
    font-size: 0.78rem; color: #6B7280; line-height: 1.6;
    border-top: 1px dashed var(--line);
    word-break: break-word;
}

/* ===== 暗色模式兜底：强制浅色变量 ===== */
.dark, .dark .gradio-container {
    --body-background-fill: #F6F7F9 !important;
    --background-fill-primary: #FFFFFF !important;
    --background-fill-secondary: #FAFBFC !important;
    --body-text-color: #1F2937 !important;
    --body-text-color-subdued: #6B7280 !important;
    --block-background-fill: #FFFFFF !important;
    --block-border-color: #E5E8EE !important;
    --border-color-primary: #E5E8EE !important;
    --border-color-accent: #2563EB !important;
    --color-accent-soft: #EFF4FE !important;
    --input-background-fill: #FFFFFF !important;
    --button-secondary-background-fill: #FFFFFF !important;
    --button-secondary-text-color: #4B5563 !important;
    color-scheme: light !important;
}
.dark .gradio-container { background: #F6F7F9 !important; }

/* 窄屏：隐藏来源侧栏，保证对话可用 */
@media (max-width: 900px) {
    .src-column { display: none !important; }
    .composer { padding: 8px 12px 10px !important; }
}
"""
