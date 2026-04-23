# 不動産資料 翻訳ツール

PowerPoint (.pptx) / PDF の資料を、レイアウトを維持したまま日本語 ⇄ 英語 ⇄ 中国語に翻訳する Streamlit アプリです。

## 特徴

- **レイアウト・画像は完全維持**：テキスト部分のみ置換
- **不動産用語に特化**：「利回り」「坪単価」「NOI」などは用語集で固定訳
- **文字溢れ対策**：翻訳後に文字が伸びた場合、自動でフォントサイズを縮小
- **2種類の翻訳エンジン**：Google翻訳（高品質・要ネット）/ LibreTranslate（オフライン・機密OK）

## 翻訳エンジン

環境変数 `TRANSLATION_ENGINE` で切替します。

| エンジン | 設定値 | 特徴 |
|---|---|---|
| Google翻訳 | `google`（デフォルト）| 品質◎・要インターネット・クラウドデプロイ向き |
| LibreTranslate | `libretranslate` | 完全オフライン・自PC完結・機密資料向き |

---

## 使い方①：Streamlit Community Cloud にデプロイ（おすすめ・共有用）

**誰でもブラウザからURLを開くだけで使える**公開URL方式です。

### 手順

1. **GitHubに非公開リポジトリを作成**
   - https://github.com/new → Private を選択
   - このフォルダを push

2. **Streamlit Community Cloudでデプロイ**
   - https://share.streamlit.io/ にアクセス（GitHubでログイン）
   - `New app` → 作成したリポジトリを選択
   - Main file path: `streamlit_app.py`
   - `Deploy` をクリック

3. **数分でデプロイ完了** → `https://<app-name>.streamlit.app/` にアクセス

※ デフォルトでGoogle翻訳エンジンが使われるため、追加設定は不要です。

---

## 使い方②：ローカルPCで実行

### 2-A. Google翻訳モード（簡単・要ネット）

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

ブラウザで http://localhost:8501 が開きます。

### 2-B. LibreTranslateモード（オフライン）

```bash
# 依存インストール
pip install -r requirements.txt
pip install libretranslate

# ターミナル①: LibreTranslate起動（初回のみモデルDL 5〜10分）
libretranslate --load-only ja,en,zh

# ターミナル②: Streamlit起動
#   事前に .env を作成し TRANSLATION_ENGINE=libretranslate を設定
streamlit run streamlit_app.py
```

`.env.example` をコピーして `.env` を作成し、`TRANSLATION_ENGINE=libretranslate` に書き換えてください。

---

## ファイル構成

```
翻訳アプリ/
├── streamlit_app.py     # Streamlit UI（エントリポイント）
├── translator.py        # 翻訳エンジン共通インターフェース
├── pptx_handler.py      # PowerPoint 翻訳処理
├── pdf_handler.py       # PDF 翻訳処理
├── glossary.py          # 不動産用語集（日英・日中・英日）
├── requirements.txt     # Python依存パッケージ
├── .env.example         # 環境変数のサンプル
└── README.md
```

## 不動産用語集のカスタマイズ

`glossary.py` の辞書に項目を追加するだけです：

```python
REAL_ESTATE_JA_EN = {
    # 既存 ...
    "サブリース": "Sublease",
    "オーナーチェンジ": "Occupied property sale",
}
```

翻訳時には、原文に含まれる用語を `__GL_0__` のような固有トークンに置き換えてから翻訳エンジンに送り、翻訳後にトークンを目標言語の固定訳へ戻す仕組みです。翻訳エンジンの訳揺れを排除できます。

## 既知の制限

- **Google翻訳**: 短時間に大量リクエストするとレート制限がかかる場合あり
- **機密資料**: Google翻訳モードでは翻訳対象テキストがGoogleのサーバに送信されます。機密資料は LibreTranslate モード（ローカル）で処理してください
- **PDF**: スキャン画像化されたPDF（OCR必要）は翻訳できません。ネイティブPDFのみ対応
- **PowerPoint**: グラフ（Chart）内のテキストは翻訳対象外
- **ファイルサイズ**: 最大 30MB（Streamlit Cloudの無料枠メモリ1GBに合わせて制限）
