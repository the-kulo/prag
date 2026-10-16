"""
离线入库脚本 — 将 PDF 文档向量化存入 ChromaDB。

用法:
    python ingest.py              # 扫描 docs/ 下所有 PDF，全量入库
    python ingest.py --reset      # 清空 collection 后重新入库
    python ingest.py docs/xx.pdf  # 增量添加指定 PDF
"""

import argparse
import hashlib
import sys
from pathlib import Path

import chromadb
import pymupdf as fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer

from config import (
    DOCS_DIR,
    CHROMA_DIR,
    COLLECTION_NAME,
    EMBED_MODEL,
    DEVICE,
    CHUNK_MIN_CHARS,
    CHUNK_MAX_CHARS,
    OVERLAP_CHARS,
    HEADING_PATTERNS,
)

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def is_heading(line: str) -> bool:
    """判断一行文本是否为标题。"""
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return False
    return any(p.match(stripped) for p in HEADING_PATTERNS)


def extract_text_from_pdf(pdf_path: Path) -> list[dict]:
    """用 PyMuPDF 逐页提取文本，返回 [{page, text}, ...]。"""
    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        print(f"  无法打开 PDF: {e}")
        return []
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append({"page": i + 1, "text": text.strip()})
    doc.close()
    return pages


def split_by_headings(pages: list[dict]) -> list[dict]:
    """按标题层级在每页内做粗切分，返回 [{page, text}] 的段落级列表。"""
    segments = []
    for p in pages:
        text = p["text"]
        lines = text.split("\n")
        current = []
        for line in lines:
            if is_heading(line) and current:
                seg_text = "\n".join(current).strip()
                if seg_text:
                    segments.append({"page": p["page"], "text": seg_text})
                current = [line]
            else:
                current.append(line)
        if current:
            seg_text = "\n".join(current).strip()
            if seg_text:
                segments.append({"page": p["page"], "text": seg_text})
    return segments


def chunk_text(text: str) -> list[str]:
    """将长文本按段落再按句子切分成 chunk，带重叠。"""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) <= CHUNK_MAX_CHARS:
            current = (current + "\n\n" + para).strip()
        else:
            if len(current) >= CHUNK_MIN_CHARS:
                chunks.append(current)
                # 重叠取末尾部分
                overlap_start = max(0, len(current) - OVERLAP_CHARS)
                current = current[overlap_start:] + "\n\n" + para
            else:
                # current 太小，继续追加
                current = (current + "\n\n" + para).strip()

    if current.strip():
        chunks.append(current.strip())

    # 如果没有生成 chunk（单段不足 CHUNK_MIN_CHARS），直接返回
    if not chunks and text.strip():
        chunks.append(text.strip())

    return chunks


def build_chunks(pages: list[dict], filename: str) -> list[dict]:
    """
    从页面列表构建带元数据的 chunk 列表。
    返回 [{id, text, metadata}]
    """
    segments = split_by_headings(pages)
    all_chunks = []
    for seg in segments:
        for chunk_text_val in chunk_text(seg["text"]):
            uid = hashlib.md5(
                f"{filename}|{seg['page']}|{chunk_text_val}".encode()
            ).hexdigest()[:16]
            all_chunks.append({
                "id": uid,
                "text": chunk_text_val,
                "metadata": {
                    "filename": filename,
                    "page": seg["page"],
                    "source_text": chunk_text_val,
                },
            })
    return all_chunks


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------


def ingest(pdf_paths: list[Path], reset: bool = False):
    """入库主函数。"""
    print(f"加载向量模型: {EMBED_MODEL}")
    model = SentenceTransformer(EMBED_MODEL, device=DEVICE)

    print(f"连接 ChromaDB: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"已删除旧 collection: {COLLECTION_NAME}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    for pdf_path in pdf_paths:
        if not pdf_path.exists():
            print(f"文件不存在，跳过: {pdf_path}")
            continue

        filename = pdf_path.name
        print(f"\n处理: {filename}")

        pages = extract_text_from_pdf(pdf_path)
        print(f"  提取 {len(pages)} 页文本")

        chunks = build_chunks(pages, filename)
        print(f"  生成 {len(chunks)} 个 chunk")

        if not chunks:
            print(f"  无有效文本，跳过")
            continue

        # 向量化
        texts = [c["text"] for c in chunks]
        ids = [c["id"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]

        print(f"  正在向量化...")
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        # 写入 ChromaDB（去重：已存在的 id 跳过）
        existing_ids = set()
        try:
            existing = collection.get(ids=ids)
            existing_ids = set(existing["ids"])
        except Exception:
            pass

        new_chunks = [
            (i, t, e, m)
            for i, t, e, m in zip(ids, texts, embeddings, metadatas)
            if i not in existing_ids
        ]

        if new_chunks:
            new_ids, new_texts, new_embeddings, new_metadatas = zip(*new_chunks)
            collection.add(
                ids=list(new_ids),
                documents=list(new_texts),
                embeddings=list(new_embeddings),
                metadatas=list(new_metadatas),
            )
            print(f"  写入 {len(new_ids)} 个新 chunk（跳过 {len(chunks) - len(new_ids)} 个重复）")
        else:
            print(f"  所有 chunk 已存在，跳过")

    count = collection.count()
    print(f"\n入库完成！Collection 共 {count} 条记录")


def main():
    parser = argparse.ArgumentParser(description="RAG 离线入库")
    parser.add_argument("pdfs", nargs="*", help="指定 PDF 文件路径")
    parser.add_argument("--reset", action="store_true", help="清空 collection 后重建")
    args = parser.parse_args()

    if args.pdfs:
        pdf_paths = [Path(p) for p in args.pdfs]
    else:
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        pdf_paths = sorted(DOCS_DIR.glob("*.pdf"))

    if not pdf_paths:
        print("未找到 PDF 文件。请将 PDF 放入 docs/ 目录，或指定文件路径。")
        sys.exit(1)

    ingest(pdf_paths, reset=args.reset)


if __name__ == "__main__":
    main()