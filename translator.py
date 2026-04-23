"""翻訳モジュール。

エンジンは環境変数 `TRANSLATION_ENGINE` で切替:
  - "google"         : Google翻訳（deep-translator経由、要ネット、品質◎）※デフォルト
  - "libretranslate" : セルフホストLibreTranslate（オフライン、機密OK）

用語集はトークン置換方式:
  1. 原文中の用語を __GL_N__ 形式のトークンに置換
  2. 翻訳エンジンに送って翻訳
  3. 翻訳結果中のトークンを目標言語の固定訳に戻す
"""

from __future__ import annotations

import os
import re

from glossary import get_glossary_entries


# UIの言語コード → 各エンジンの言語コード
_GOOGLE_LANG_MAP = {"ja": "ja", "en": "en", "zh": "zh-CN"}
_LIBRE_LANG_MAP = {"ja": "ja", "en": "en", "zh": "zh"}

# LibreTranslate で直接モデルが存在しないペア（Englishをpivot）
_LIBRE_PIVOT_PAIRS = {("ja", "zh"), ("zh", "ja")}

_TOKEN_RE = re.compile(r"__GL_\d+__")


def _current_engine() -> str:
    return os.getenv("TRANSLATION_ENGINE", "google").lower()


# ============================================================
# Google 翻訳バックエンド（deep-translator）
# ============================================================

def _google_translate(texts: list[str], source: str, target: str) -> list[str]:
    """Google翻訳で一括翻訳する。長文は5000文字ごとに分割。"""
    from deep_translator import GoogleTranslator

    src = _GOOGLE_LANG_MAP.get(source, source)
    tgt = _GOOGLE_LANG_MAP.get(target, target)

    translator = GoogleTranslator(source=src, target=tgt)
    output: list[str] = []
    for t in texts:
        if not t or not t.strip():
            output.append(t)
            continue
        try:
            result = translator.translate(t)
            output.append(result if result is not None else t)
        except Exception:
            # 1件の失敗で全体を止めない
            output.append(t)
    return output


# ============================================================
# LibreTranslate バックエンド
# ============================================================

def _libretranslate_url() -> str:
    return os.getenv("LIBRETRANSLATE_URL", "http://localhost:5000").rstrip("/")


def _libre_http_translate(texts: list[str], source: str, target: str) -> list[str]:
    """LibreTranslateのHTTPエンドポイントに一括翻訳を投げる。"""
    import httpx

    url = f"{_libretranslate_url()}/translate"
    payload = {
        "q": texts,
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

    result = data.get("translatedText", "")
    if isinstance(result, str):
        return [result]
    return list(result)


def _libre_translate(texts: list[str], source: str, target: str) -> list[str]:
    """LibreTranslateで翻訳。直接ペアがなければEnglish経由でpivotする。"""
    src = _LIBRE_LANG_MAP.get(source, source)
    tgt = _LIBRE_LANG_MAP.get(target, target)
    if (source, target) in _LIBRE_PIVOT_PAIRS:
        via_en = _libre_http_translate(texts, src, "en")
        return _libre_http_translate(via_en, "en", tgt)
    return _libre_http_translate(texts, src, tgt)


# ============================================================
# エンジン共通ディスパッチ
# ============================================================

def _translate_chunk(texts: list[str], source: str, target: str) -> list[str]:
    engine = _current_engine()
    if engine == "libretranslate":
        return _libre_translate(texts, source, target)
    return _google_translate(texts, source, target)


# ============================================================
# 用語集保護
# ============================================================

def _protect_terms(text: str, source_lang: str, target_lang: str) -> tuple[str, dict[str, str]]:
    """原文中の用語を __GL_N__ トークンに置換し、トークン→目標訳の辞書を返す。"""
    entries = get_glossary_entries(source_lang.upper(), target_lang.upper())
    if not entries:
        return text, {}

    token_map: dict[str, str] = {}
    modified = text
    counter = 0
    for src_term, tgt_term in sorted(entries.items(), key=lambda kv: -len(kv[0])):
        if src_term in modified:
            token = f"__GL_{counter}__"
            modified = modified.replace(src_term, token)
            token_map[token] = tgt_term
            counter += 1
    return modified, token_map


def _unprotect_terms(translated: str, token_map: dict[str, str]) -> str:
    """翻訳結果中のトークンを目標訳に戻す。未解決トークンは削除。"""
    if not token_map:
        return translated
    for token, target in token_map.items():
        translated = translated.replace(token, target)
    translated = _TOKEN_RE.sub("", translated)
    return translated


# ============================================================
# 公開関数
# ============================================================

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

    if source_lang not in {"ja", "en", "zh"} or target_lang not in {"ja", "en", "zh"}:
        raise ValueError(f"未対応の言語コード: {source_lang} → {target_lang}")

    indices = [i for i, t in enumerate(texts) if t and t.strip()]
    if not indices:
        return list(texts)

    protected: list[str] = []
    token_maps: list[dict[str, str]] = []
    for i in indices:
        protected_text, tmap = _protect_terms(texts[i], source_lang, target_lang)
        protected.append(protected_text)
        token_maps.append(tmap)

    BATCH = 50
    translated_all: list[str] = []
    for start in range(0, len(protected), BATCH):
        chunk = protected[start : start + BATCH]
        result = _translate_chunk(chunk, source_lang, target_lang)
        translated_all.extend(result)

    output = list(texts)
    for idx, translated, tmap in zip(indices, translated_all, token_maps):
        output[idx] = _unprotect_terms(translated, tmap)
    return output
