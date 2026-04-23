"""PDF の翻訳。画像・レイアウトを保ったままテキストのみを差し替える。

アプローチ:
  1. page.get_text("dict") で文字ブロックの位置・サイズ・色を取得
  2. 元テキスト位置に白矩形でマスク（画像は触らない）
  3. 翻訳文を同じ bbox に insert_textbox で再配置
  4. 溢れる場合はフォントサイズを段階的に縮小して再試行
"""

from __future__ import annotations

from io import BytesIO

import fitz  # PyMuPDF

from translator import translate_texts


# 言語コード → PyMuPDF内蔵CJKフォント
# 内蔵フォントは Latin 文字も表示可能
_CJK_FONTS = {
    "JA": "japan",
    "ZH": "china-s",
    "ZH-HANS": "china-s",
    "ZH-HANT": "china-t",
    "KO": "korea",
}


def _pick_font(target_lang: str) -> str:
    base = target_lang.upper().split("-")[0]
    if base == "ZH":
        return _CJK_FONTS["ZH"]
    return _CJK_FONTS.get(base, "helv")


def _collect_lines(page) -> list[dict]:
    """行単位でテキストブロックを収集。span単位だと細切れすぎて翻訳精度が落ちるため。"""
    data = page.get_text("dict")
    lines = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:  # 0=テキスト、1=画像
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s.get("text", "") for s in spans)
            if not text.strip():
                continue

            # 行のbboxはspansを包含するものを計算
            x0 = min(s["bbox"][0] for s in spans)
            y0 = min(s["bbox"][1] for s in spans)
            x1 = max(s["bbox"][2] for s in spans)
            y1 = max(s["bbox"][3] for s in spans)

            # 先頭spanの属性を代表値とする
            first = spans[0]
            color_int = first.get("color", 0)
            # intカラー → (r,g,b) 0-1
            r = ((color_int >> 16) & 0xFF) / 255
            g = ((color_int >> 8) & 0xFF) / 255
            b = (color_int & 0xFF) / 255

            lines.append({
                "text": text,
                "bbox": fitz.Rect(x0, y0, x1, y1),
                "fontsize": first.get("size", 11),
                "color": (r, g, b),
            })
    return lines


def _insert_fitting_text(
    page,
    rect: fitz.Rect,
    text: str,
    fontsize: float,
    fontname: str,
    color: tuple,
) -> None:
    """bboxに収まるようフォントサイズを自動調整して挿入する。"""
    # 訳文が長い場合は縦方向に少し余裕を持たせる（下方向に最大1.5倍まで拡張）
    expandable = fitz.Rect(
        rect.x0,
        rect.y0,
        rect.x1,
        rect.y1 + (rect.height * 0.5),
    )

    size = fontsize
    min_size = max(fontsize * 0.6, 6.0)  # 元の60%未満にはしない

    while size >= min_size:
        result = page.insert_textbox(
            rect,
            text,
            fontsize=size,
            fontname=fontname,
            color=color,
            align=fitz.TEXT_ALIGN_LEFT,
        )
        if result >= 0:
            return
        size *= 0.92

    # それでも入らないなら少し拡張した箱に最小サイズで強制挿入
    page.insert_textbox(
        expandable,
        text,
        fontsize=min_size,
        fontname=fontname,
        color=color,
        align=fitz.TEXT_ALIGN_LEFT,
    )


def translate_pdf(
    input_bytes: bytes,
    target_lang: str,
    source_lang: str = "ja",
) -> bytes:
    """PDFバイト列を受け取り、翻訳済みのPDFバイト列を返す。

    Args:
        target_lang / source_lang: UI言語コード（"ja" / "en" / "zh"）
    """
    doc = fitz.open(stream=input_bytes, filetype="pdf")
    fontname = _pick_font(target_lang)

    # ページごとに行を収集 → まとめて翻訳 → 再配置
    for page in doc:
        lines = _collect_lines(page)
        if not lines:
            continue

        texts = [line["text"] for line in lines]
        translated = translate_texts(texts, target_lang, source_lang)

        # 元テキストを白矩形でマスク（画像領域は redact_annot の範囲外なので触らない）
        for line in lines:
            page.add_redact_annot(line["bbox"], fill=(1, 1, 1))
        # images=PDF_REDACT_IMAGE_NONE で画像は絶対に削除されない
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

        # 翻訳文を同位置に挿入
        for line, new_text in zip(lines, translated):
            _insert_fitting_text(
                page,
                line["bbox"],
                new_text,
                fontsize=line["fontsize"],
                fontname=fontname,
                color=line["color"],
            )

    output = BytesIO()
    doc.save(output, garbage=3, deflate=True)
    doc.close()
    return output.getvalue()
