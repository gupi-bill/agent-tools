"""ai: AI / Agent 工具。"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def register(parent: argparse.ArgumentParser) -> None:
    sub = parent.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("token-count", help="计算 token 数")
    p.add_argument("text", nargs="?", help="输入文本")
    p.add_argument("--file", "-f", help="从文件读取")
    p.add_argument("--model", default="gpt-4", help="模型名称（用于估算）")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("prompt-template", help="生成 prompt 模板")
    p.add_argument("--name", required=True, help="模板名")
    p.add_argument("--variables", help="变量列表（逗号分隔）")
    p.add_argument("--output", "-o")
    p.add_argument("--format", choices=["jinja2", "python", "mustache"], default="python")

    p = sub.add_parser("json-schema-gen", help="从 JSON 示例生成 Schema")
    p.add_argument("input")
    p.add_argument("--output", "-o")

    p = sub.add_parser("rag-index", help="RAG 文档索引")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ext", default=".md,.txt,.py,.js,.ts")
    p.add_argument("--output", "-o", default="rag_index.json")

    p = sub.add_parser("similarity", help="文本相似度计算")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--method", choices=["cosine", "jaccard", "levenshtein"], default="cosine")

    p = sub.add_parser("classify", help="文本分类")
    p.add_argument("text")
    p.add_argument("--categories", required=True, help="分类列表（逗号分隔）")
    p.add_argument("--method", choices=["keyword", "tfidf"], default="keyword")

    p = sub.add_parser("summarize", help="文本摘要（TF-IDF 关键词提取）")
    p.add_argument("text", nargs="?")
    p.add_argument("--file", "-f", help="从文件读取")
    p.add_argument("--sentences", type=int, default=3)

    p = sub.add_parser("keyword-extract", help="关键词提取")
    p.add_argument("text", nargs="?")
    p.add_argument("--file", "-f", help="从文件读取")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--min-length", type=int, default=2)

    p = sub.add_parser("sentiment", help="简单情感分析")
    p.add_argument("text")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("stopwords", help="停用词管理")
    p.add_argument("--lang", choices=["en", "zh", "ja", "ko"], default="en")
    p.add_argument("--add", help="添加停用词")
    p.add_argument("--remove", help="移除停用词")
    p.add_argument("--list", action="store_true")

    p = sub.add_parser("nltk-test", help="NLTK 检测")
    p.add_argument("--list-corpora", action="store_true")
    p.add_argument("--download", help="下载语料")

    p = sub.add_parser("embedding-dim", help="检测 embedding 维度")
    p.add_argument("text")
    p.add_argument("--provider", choices=["openai", "azure", "ollama", "local"], default="local")
def _estimate_tokens(text: str, model: str = "gpt-4") -> int:
    """粗略估算 token 数。"""
    if model.startswith("gpt-4"):
        # ~4 chars per token for English
        return max(1, len(text) // 4)
    elif model.startswith("gpt-3.5"):
        return max(1, len(text) // 4)
    elif "claude" in model.lower():
        return max(1, len(text) // 3)
    else:
        return max(1, len(text) // 4)


def cmd_token_count(args: argparse.Namespace) -> int:
    text = args.text or ""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="ignore")
    tokens = _estimate_tokens(text, args.model)
    chars = len(text)
    words = len(text.split())
    result = {"model": args.model, "tokens": tokens, "characters": chars, "words": words}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"📝 Token 估算")
        print(f"   模型: {args.model}")
        print(f"   字符: {chars:,}")
        print(f"   单词: {words:,}")
        print(f"   估算 Token: {tokens:,}")
    return 0



def cmd_prompt_template(args: argparse.Namespace) -> int:
    name = args.name
    variables = [v.strip() for v in (args.variables or "").split(",") if v.strip()] if args.variables else []
    out = Path(args.output) if args.output else Path(f"prompt_{name}.py")
    lines = [f'"""{name} prompt template."""', 'from __future__ import annotations', '', '']
    if variables:
        lines.append(f'def render_{name.replace("-", "_")}(' + ', '.join(variables) + f') -> str:')
        lines.append('    """Render the prompt template."""')
        lines.append('    return f"""')
        lines.append('    <SYSTEM>')
        lines.append('    You are a professional AI assistant.')
        lines.append('    </SYSTEM>')
        lines.append('')
        lines.append('    <USER>')
        for v in variables:
            lines.append(f'    {v}={{{{{v}}}}}')
        lines.append('    </USER>')
        lines.append('    """')
    else:
        lines.append('def render_prompt() -> str:')
        lines.append('    return """')
        lines.append('    <SYSTEM>AI Assistant</SYSTEM>')
        lines.append('    """')
    content = '\n'.join(lines) + '\n'
    out.write_text(content, encoding="utf-8")
    print(f"✅ Prompt 模板已生成 → {out}")
    return 0
def cmd_json_schema_gen(args: argparse.Namespace) -> int:
    import json as _json
    data = _json.loads(Path(args.input).read_text(encoding="utf-8"))
    def _schema(obj: Any) -> dict:
        if isinstance(obj, dict):
            return {"type": "object", "properties": {k: _schema(v) for k, v in obj.items()}}
        elif isinstance(obj, list):
            return {"type": "array", "items": _schema(obj[0]) if obj else {}}
        elif isinstance(obj, bool):
            return {"type": "boolean"}
        elif isinstance(obj, int):
            return {"type": "integer"}
        elif isinstance(obj, float):
            return {"type": "number"}
        elif isinstance(obj, str):
            return {"type": "string"}
        elif obj is None:
            return {"type": "null"}
        return {}
    schema = _schema(data)
    out = Path(args.output) if args.output else Path(args.input).with_suffix(".schema.json")
    out.write_text(_json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Schema 已生成 → {out}")
    return 0


def cmd_rag_index(args: argparse.Namespace) -> int:
    root = Path(args.path).resolve()
    exts = tuple(args.ext.split(","))
    chunks: list[dict] = []
    chunk_size = 500
    overlap = 50
    for f in root.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            sentences = re.split(r"[。.!!?；\n]", text)
            current = []
            current_len = 0
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                current.append(sent)
                current_len += len(sent)
                if current_len >= chunk_size:
                    chunks.append({
                        "source": str(f.relative_to(root)),
                        "content": " ".join(current),
                        "char_count": current_len,
                    })
                    current = current[-(current_len - overlap)//max(1, chunk_size//2):] if current else []
                    current_len = sum(len(s) for s in current)
            if current:
                chunks.append({"source": str(f.relative_to(root)), "content": " ".join(current), "char_count": sum(len(s) for s in current)})
    out = Path(args.output)
    out.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ RAG 索引已生成 → {out} ({len(chunks)} 个片段)")
    return 0


def cmd_similarity(args: argparse.Namespace) -> int:
    a = args.a.lower()
    b = args.b.lower()
    if args.method == "cosine":
        from collections import Counter
        ca = Counter(a.split())
        cb = Counter(b.split())
        all_words = set(ca) | set(cb)
        dot = sum(ca.get(w, 0) * cb.get(w, 0) for w in all_words)
        mag_a = sum(v**2 for v in ca.values()) ** 0.5
        mag_b = sum(v**2 for v in cb.values()) ** 0.5
        score = dot / (mag_a * mag_b) if mag_a and mag_b else 0
    elif args.method == "jaccard":
        sa = set(a.split())
        sb = set(b.split())
        score = len(sa & sb) / len(sa | sb) if sa | sb else 0
    else:
        # Levenshtein
        m, n = len(a), len(b)
        dp = [[0]*(n+1) for _ in range(m+1)]
        for i in range(m+1): dp[i][0] = i
        for j in range(n+1): dp[0][j] = j
        for i in range(1, m+1):
            for j in range(1, n+1):
                if a[i-1] == b[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        score = 1 - dp[m][n] / max(m, n)
    print(f"  相似度: {score:.4f}  ({args.method})")
    print(f"  A: {a[:60]}...")
    print(f"  B: {b[:60]}...")
    return 0


def cmd_classify(args: argparse.Namespace) -> int:
    categories = [c.strip() for c in args.categories.split(",")]
    text = args.text.lower()
    scores: dict[str, float] = {}
    for cat in categories:
        keywords = cat.lower().split()
        matches = sum(1 for kw in keywords if kw in text)
        scores[cat] = matches / len(keywords) if keywords else 0
    best = max(scores.items(), key=lambda x: x[1])
    print(f"📂 分类结果: {best[0]} (得分: {best[1]:.2f})")
    for cat, score in sorted(scores.items(), key=lambda x: -x[1]):
        bar = "█" * int(score * 20)
        print(f"   {cat:<15} {score:.2f}  {bar}")
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    text = args.text or ""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="ignore")
    sentences = re.split(r"[。.!!?；\n]", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    from collections import Counter
    words = Counter(text.lower().split())
    total = len(text.split())
    scores = {}
    for i, sent in enumerate(sentences):
        score = sum(words.get(w, 0) for w in sent.lower().split()) / max(1, len(sent.split()))
        scores[i] = score
    top_indices = sorted(scores, key=scores.get, reverse=True)[:args.sentences]
    summary = " ".join(sentences[i] for i in sorted(top_indices))
    print(summary)
    return 0


def cmd_keyword_extract(args: argparse.Namespace) -> int:
    text = args.text or ""
    if args.file:
        text = Path(args.file).read_text(encoding="utf-8", errors="ignore")
    from collections import Counter
    words = [w for w in text.lower().split() if len(w) >= args.min_length]
    freq = Counter(words)
    total = len(words)
    scored = {w: n/total for w, n in freq.items() if n >= 2}
    top = sorted(scored.items(), key=lambda x: -x[1])[:args.top]
    for w, s in top:
        bar = "█" * int(s * 100)
        print(f"  {w:<20} {s:.3f}  {bar}")
    return 0


def cmd_sentiment(args: argparse.Namespace) -> int:
    text = args.text.lower()
    positive = ["good", "great", "excellent", "amazing", "love", "best", "perfect", "happy", "wonderful", "fantastic", "喜欢", "好", "棒", "优秀", "开心", "爱"]
    negative = ["bad", "terrible", "awful", "hate", "worst", "horrible", "sad", "angry", "bug", "error", "fail", "糟糕", "差", "烂", "讨厌", "生气", "错误"]
    pos_count = sum(1 for w in positive if w in text)
    neg_count = sum(1 for w in negative if w in text)
    total = pos_count + neg_count
    if total == 0:
        result = {"sentiment": "neutral", "score": 0.0, "positive": pos_count, "negative": neg_count}
    else:
        score = (pos_count - neg_count) / total
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        result = {"sentiment": sentiment, "score": round(score, 3), "positive": pos_count, "negative": neg_count}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        emoji = {"positive": "😊", "negative": "😠", "neutral": "😐"}
        print(f"  {emoji.get(result['sentiment'], '😐')} 情感: {result['sentiment']}  (分数: {result['score']:+.3f})")
        print(f"     正面: {result['positive']}  负面: {result['negative']}")
    return 0


def cmd_stopwords(args: argparse.Namespace) -> int:
    lang = args.lang
    default_sw = {
        "en": ["a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "shall", "not", "no", "nor", "so", "if", "then", "than", "too", "very", "just", "about", "above", "after", "again", "all", "also", "any", "because", "before", "between", "both", "but", "each", "few", "more", "most", "other", "out", "over", "own", "same", "some", "such", "through", "under", "until", "up", "we", "me", "my", "i", "you", "your", "he", "she", "it", "they", "them", "their", "its", "his", "her"],
        "zh": ["的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"],
    }
    sw = default_sw.get(lang, default_sw["en"])
    if args.add:
        for word in args.add.split(","):
            sw.append(word.strip())
        print(f"  已添加: {word.strip()}")
    if args.remove:
        for word in args.remove.split(","):
            if word.strip() in sw:
                sw.remove(word.strip())
        print(f"  已移除: {word.strip()}")
    if args.list:
        print(f"  {lang} 停用词 ({len(sw)} 个):")
        print("  " + " ".join(sw[:50]))
    return 0


def cmd_nltk_test(args: argparse.Namespace) -> int:
    try:
        import nltk
        if args.list_corpora:
            print("  NLTK 语料库:")
            for name in dir(nltk.corpus):
                if not name.startswith("_"):
                    print(f"    - {name}")
        if args.download:
            nltk.download(args.download)
            print(f"  ✅ 已下载 {args.download}")
        else:
            print(f"  NLTK 已安装，版本: {nltk.__version__}")
    except ImportError:
        print("  ❌ 请安装 NLTK: pip install nltk")
    return 0


def cmd_embedding_dim(args: argparse.Namespace) -> int:
    text = args.text
    provider = args.provider
    if provider == "openai":
        dim = 1536  # text-embedding-ada-002
    elif provider == "azure":
        dim = 1536
    elif provider == "ollama":
        dim = 768  # default nomic-embed-text
    else:
        dim = 384  # all-MiniLM-L6-v2
    print(f"  提供商: {provider}")
    print(f"  默认维度: {dim}")
    print(f"  输入文本长度: {len(text)} 字符")
    return 0
