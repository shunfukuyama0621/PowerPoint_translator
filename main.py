"""FastAPI エントリポイント。

ファイルアップロード → 翻訳 → ダウンロード の1本道エンドポイント。
翻訳は LibreTranslate（セルフホスト）を利用。
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from pdf_handler import translate_pdf
from pptx_handler import translate_pptx


load_dotenv()

app = FastAPI(title="不動産資料 翻訳ツール")

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

SUPPORTED_LANGS = {"ja", "en", "zh"}


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/translate")
async def translate(
    file: UploadFile = File(...),
    source_lang: str = Form("ja"),
    target_lang: str = Form("en"),
):
    filename = file.filename or ""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if ext not in {"pptx", "pdf"}:
        raise HTTPException(status_code=400, detail="対応形式は .pptx と .pdf のみです")

    if source_lang not in SUPPORTED_LANGS or target_lang not in SUPPORTED_LANGS:
        raise HTTPException(status_code=400, detail="言語コードが不正です")
    if source_lang == target_lang:
        raise HTTPException(status_code=400, detail="翻訳元と翻訳先が同じです")

    data = await file.read()
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"ファイルサイズは {MAX_FILE_SIZE // 1024 // 1024}MB 以下にしてください",
        )

    try:
        if ext == "pptx":
            translated_bytes = translate_pptx(
                data, target_lang=target_lang, source_lang=source_lang
            )
            media_type = (
                "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        else:
            translated_bytes = translate_pdf(
                data, target_lang=target_lang, source_lang=source_lang
            )
            media_type = "application/pdf"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻訳処理中にエラー: {e}")

    base, _ = os.path.splitext(filename)
    out_name = f"{base}_{target_lang}.{ext}"

    return Response(
        content=translated_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="translated.{ext}"; '
                f"filename*=UTF-8''{out_name}"
            ),
        },
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
