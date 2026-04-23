# 不動産資料 翻訳ツール

PowerPoint (.pptx) / PDF の資料を、レイアウトを維持したまま日本語 ⇄ 英語 ⇄ 中国語に翻訳する社内ツール。
翻訳エンジンに **LibreTranslate** をセルフホストしているため、**完全無料・無制限**で利用できます（APIキー・クレカ登録不要）。

## 特徴

- **レイアウト・画像は完全維持**：テキスト部分のみ置換。図版や写真は一切触りません
- **不動産用語に特化**：「利回り」「坪単価」「NOI」など業界用語は用語集で固定訳に
- **文字溢れ対策**：翻訳後に文字が伸びた場合、自動でフォントサイズを縮小
- **完全オフライン動作**：社内ネットワーク内で完結、外部にデータを送信しません

## 動作要件

| 項目 | 必要スペック |
|------|-------------|
| OS | Windows 10/11、macOS、Linux |
| RAM | **空き 2GB 以上** |
| ディスク | 空き 3GB 以上 |
| ソフトウェア | **Docker Desktop**（Windows/Mac）または Docker Engine（Linux） |

※ Docker Desktop のインストール: https://www.docker.com/products/docker-desktop/

## セットアップ

### 1. このフォルダを動かしたいPCにコピー

USBメモリでもGitHubでも、どんな方法でも構いません。

### 2. Docker Desktop を起動

初回起動時は Windows Subsystem for Linux (WSL) のセットアップが走ることがあります。Docker Desktop がタスクトレイで「Docker Desktop is running」と表示されればOK。

### 3. アプリを起動

フォルダ内で以下を実行：

```bash
docker compose up -d
```

- **初回のみ**: LibreTranslate のイメージ取得 + 言語モデル（ja/en/zh）のダウンロードで5〜10分かかります
- 2回目以降は10秒ほどで起動します

### 4. ブラウザでアクセス

http://localhost:8000

**同じLAN内の別PCやスマホからもアクセス可能**です：  
サーバPCのIPアドレス（例: `192.168.1.100`）を確認して `http://192.168.1.100:8000` を開いてください。

### 停止・再起動

```bash
# 停止
docker compose down

# 再起動
docker compose up -d

# ログを見る
docker compose logs -f
```

## 使い方

1. 翻訳元・翻訳先の言語を選択（日本語 / 英語 / 中国語）
2. `.pptx` または `.pdf` ファイルをドラッグ&ドロップ（最大20MB）
3. 「翻訳を実行」をクリック
4. 翻訳後のファイルが自動ダウンロードされる

## ファイル構成

```
翻訳アプリ/
├── docker-compose.yml   # LibreTranslate + FastAPI のオーケストレーション
├── Dockerfile           # FastAPIアプリのコンテナ化
├── main.py              # FastAPI エンドポイント
├── translator.py        # LibreTranslate HTTP クライアント + 用語集保護
├── pptx_handler.py      # PowerPoint 翻訳処理
├── pdf_handler.py       # PDF 翻訳処理
├── glossary.py          # 不動産用語集（日英・日中・英日）
├── requirements.txt     # Python依存パッケージ
├── static/
│   └── index.html       # フロントUI
├── .env.example
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

保存後、`docker compose restart app` で反映されます。

翻訳時には、原文に含まれる用語を `__GL_0__` のような固有トークンに置き換えてからLibreTranslateに送り、翻訳後にトークンを目標言語の固定訳へ戻す仕組みです。これにより**翻訳エンジンの気まぐれな訳揺れを完全に排除**できます。

## 既知の制限

- **翻訳品質**: DeepL や Google Translate より1ランク劣ります。特に日本語の敬語・長文の文脈理解は苦手。最終的には**人による校正が前提**の用途向けです
- **PDF**: スキャン画像化されたPDF（OCR必要）は翻訳できません。ネイティブPDFのみ対応
- **PowerPoint**: グラフ（Chart）内のテキストは翻訳対象外
- **ja ⇔ zh**: LibreTranslate には直接モデルがないため、**English を経由するpivot翻訳**になります（精度がさらに落ちる可能性あり）
- **初回起動**: 言語モデルのダウンロードで5〜10分程度かかります

## トラブルシューティング

### ポート 8000 / 5000 が既に使われている
`docker-compose.yml` の `ports:` を `"8080:8000"` のように変更してください。

### メモリ不足でコンテナが落ちる
Docker Desktop の設定でメモリ割り当てを4GB以上に増やしてください（Settings → Resources）。

### 翻訳が極端に遅い・タイムアウトする
サーバPCのCPU使用率を確認。古いPCの場合は1ファイルに数分かかることがあります。CPUが弱い場合は、1度に翻訳するスライド数を減らしてください。

### LibreTranslate が起動しない
初回のモデルダウンロードに失敗している可能性があります。ログで確認：
```bash
docker compose logs libretranslate
```
