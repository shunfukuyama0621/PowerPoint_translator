"""Streamlit UI for 不動産資料 翻訳ツール。

既存の translator / pdf_handler / pptx_handler をそのまま利用し、
FastAPI の代わりに Streamlit でアップロード → 翻訳 → ダウンロードを提供する。

起動:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from pdf_handler import translate_pdf
from pptx_handler import translate_pptx


load_dotenv()

MAX_FILE_SIZE = 30 * 1024 * 1024  # 30MB

LANG_OPTIONS = {
    "日本語": "ja",
    "英語 (English)": "en",
    "中国語 (中文)": "zh",
}


st.set_page_config(
    page_title="不動産資料 翻訳ツール",
    page_icon="📄",
    layout="centered",
)

st.title("📄 不動産資料 翻訳ツール")
st.caption(
    "PowerPoint (.pptx) / PDF の資料を、レイアウトを維持したまま翻訳します。"
    "画像・図版はそのまま、テキストのみ差し替えます。"
)

with st.sidebar:
    st.header("⚙️ 設定")
    engine = os.getenv("TRANSLATION_ENGINE", "google").lower()
    if engine == "libretranslate":
        lt_url = os.getenv("LIBRETRANSLATE_URL", "http://localhost:5000")
        st.markdown(f"**翻訳エンジン**: 🔒 LibreTranslate\n\n`{lt_url}`")
    else:
        st.markdown("**翻訳エンジン**: 🌐 Google翻訳")
    st.markdown(
        "- 用語集: `glossary.py`\n"
        "- 対応形式: `.pptx` / `.pdf`\n"
        f"- 最大サイズ: {MAX_FILE_SIZE // 1024 // 1024}MB"
    )

col1, col2 = st.columns(2)
with col1:
    source_label = st.selectbox("翻訳元", list(LANG_OPTIONS.keys()), index=0)
with col2:
    target_label = st.selectbox("翻訳先", list(LANG_OPTIONS.keys()), index=1)

source_lang = LANG_OPTIONS[source_label]
target_lang = LANG_OPTIONS[target_label]

uploaded = st.file_uploader(
    f"ファイルをアップロード（.pptx または .pdf、最大{MAX_FILE_SIZE // 1024 // 1024}MB）",
    type=["pptx", "pdf"],
    accept_multiple_files=False,
)

translate_clicked = st.button("🚀 翻訳を実行", type="primary", use_container_width=True)

if translate_clicked:
    if uploaded is None:
        st.warning("ファイルを選択してください。")
        st.stop()

    if source_lang == target_lang:
        st.error("翻訳元と翻訳先が同じです。異なる言語を選んでください。")
        st.stop()

    data = uploaded.getvalue()
    if len(data) > MAX_FILE_SIZE:
        st.error(
            f"ファイルサイズが {MAX_FILE_SIZE // 1024 // 1024}MB を超えています。"
        )
        st.stop()

    filename = uploaded.name
    ext = Path(filename).suffix.lower().lstrip(".")

    progress = st.progress(0, text="翻訳を開始しています…")

    try:
        progress.progress(20, text="ファイルを解析中…")

        if ext == "pptx":
            progress.progress(40, text="PowerPoint を翻訳中…")
            translated_bytes = translate_pptx(
                data, target_lang=target_lang, source_lang=source_lang
            )
            mime = (
                "application/vnd.openxmlformats-officedocument."
                "presentationml.presentation"
            )
        elif ext == "pdf":
            progress.progress(40, text="PDF を翻訳中…")
            translated_bytes = translate_pdf(
                data, target_lang=target_lang, source_lang=source_lang
            )
            mime = "application/pdf"
        else:
            st.error("対応形式は .pptx と .pdf のみです。")
            st.stop()

        progress.progress(100, text="完了！")
    except Exception as e:
        progress.empty()
        st.error(f"翻訳処理中にエラーが発生しました: {e}")
        if engine == "libretranslate":
            st.info(
                "LibreTranslate が起動しているか、`LIBRETRANSLATE_URL` が正しいかを確認してください。"
            )
        else:
            st.info(
                "インターネット接続を確認してください。"
                "Google翻訳の一時的な制限にかかっている可能性があります。"
            )
        st.stop()

    base = Path(filename).stem
    out_name = f"{base}_{target_lang}.{ext}"

    st.success(f"翻訳が完了しました（{source_label} → {target_label}）")
    st.download_button(
        label=f"💾 {out_name} をダウンロード",
        data=translated_bytes,
        file_name=out_name,
        mime=mime,
        use_container_width=True,
    )
