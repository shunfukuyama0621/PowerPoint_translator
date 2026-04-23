"""LibreTranslate（セルフホスト）を利用した翻訳モジュール。

用語集はトークン置換方式:
  1. 原文中の用語を __GL_N__ 形式のトークンに置換
  2. LibreTranslate に送って翻訳
  3. 翻訳結果中のトークンを目標言語の固定訳に戻す

ja⇔zh の直接モデルが存在しない場合は English をpivotにして翻訳する。
"""

from __future__ import annotations

import os
import re

import httpx

from glossary import get_glossary_entries


# UIの言語コード → LibreTranslate の言語コード
_LANG_MAP = {"ja": "ja", "en": "en", "zh": "zh"}

# 直接モデルが存在しないと想定されるペア（必要に応じてpivot経由に切替）
_PIVOT_PAIRS = {("ja", "zh"), ("zh", "ja")}

_TOKEN_RE = re.compile(r"__GL_\d+__")


def _libretranslate_url() -> str:
    return os.getenv("LIBRETRANSLATE_URL", "http://localhost:5000").rstrip("/")


def _http_translate(texts: list[str], source: str, target: str) -> list[str]:
    """LibreTranslateのHTTPエンドポイントに一括翻訳を投げる。"""
    url = f"{_libretranslate_url()}/translate"
    payload = {
        "q": texts,  # LibreTranslate は文字列配列も受け付ける
        "source": source,
        "target": target,
        "format": "text",
    }
    api_key = os.getenv("LIBRETRANSLATE_API_KEY")
    if api_key:
        payload["api_key"] = api_key

    with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    # LibreTranslate のレスポンス仕様: 文字列1件なら {"translatedText": "..."}、
    # 配列なら {"translatedText": [...]}
    result = data.get("translatedText", "")
    if isinstance(result, str):
        return [result]
    return list(result)


def _translate_chunk(texts: list[str], source: str, target: str) -> list[str]:
    """LibreTranslateを1回呼ぶ。直接ペアがなければEnglish経由でpivotする。"""
    if (source, target) in _PIVOT_PAIRS:
        # ja ⇔ zh などの直接モデルがないケース: English を中継
        via_en = _http_translate(texts, source, "en")
        return _http_translate(via_en, "en", target)
    return _http_translate(texts, source, target)


def _protect_terms(text: str, source_lang: str, target_lang: str) -> tuple[str, dict[str, str]]:
    """原文中の用語を __GL_N__ トークンに置換し、トークン→目標訳の辞書を返す。

    トークンは数字と下線のみで構成されるので、翻訳中に単語として訳されにくい。
    """
    entries = get_glossary_entries(source_lang.upper(), target_lang.upper())
    if not entries:
        return text, {}

    token_map: dict[str, str] = {}
    modified = text
    counter = 0
    # 長い用語から先にマッチ（部分一致の競合回避）
    for src_term, tgt_term in sorted(entries.items(), key=lambda kv: -len(kv[0])):
        if src_term in modified:
            token = f"__GL_{counter}__"
            modified = modified.replace(src_term, token)
            token_map[token] = tgt_term
            counter += 1
    return modified, token_map


def _unprotect_terms(translated: str, token_map: dict[str, str]) -> str:
    """翻訳結果中のトークンを目標訳に戻す。"""
    if not token_map:
        return translated
    for token, target in token_map.items():
        translated = translated.replace(token, target)
    # 未解決トークンが残っていたら空文字にして不自然な表示を避ける
    translated = _TOKEN_RE.sub("", translated)
    return translated


def translate_texts(
    texts: list[str],
    target_lang: str,
    source_lang: str = "ja",
) -> list[str]:
    """UIの言語コード（ja/en/zh）を受け取って一括翻訳する。

    Args:
        texts: 翻訳対象のテキスト一覧（空文字は翻訳せずそのまま返す）
        target_lang / source_lang: "ja" / "en" / "zh"
    """
    if not texts:
        return []

    lt_target = _LANG_MAP.get(target_lang)
    lt_source = _LANG_MAP.get(source_lang)
    if not lt_target or not lt_source:
        raise ValueError(f"未対応の言語コード: {source_lang} → {target_lang}")

    indices = [i for i, t in enumerate(texts) if t and t.strip()]
    if not indices:
        return list(texts)

    # 用語保護: 各テキストごとにトークン置換
    protected = []
    token_maps = []
    for i in indices:
        protected_text, tmap = _protect_terms(texts[i], source_lang, target_lang)
        protected.append(protected_text)
        token_maps.append(tmap)

    # 大量テキストの場合に備えてチャンクで送信
    BATCH = 50
    translated_all: list[str] = []
    for start in range(0, len(protected), BATCH):
        chunk = protected[start : start + BATCH]
        result = _translate_chunk(chunk, lt_source, lt_target)
        translated_all.extend(result)

    # 用語復元
    output = list(texts)
    for idx, translated, tmap in zip(indices, translated_all, token_maps):
        output[idx] = _unprotect_terms(translated, tmap)
    return output
