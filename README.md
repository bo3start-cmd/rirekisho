# 履歴書自動生成Webアプリ

## 機能
- 候補者がフォームに入力→JIS規格の履歴書PDFを自動生成・ダウンロード
- 管理者ログインで履歴書一覧・氏名検索・PDF一括ダウンロード

## ローカル起動
```bash
cd resume_app
python setup_fonts.py          # フォントセットアップ（初回のみ）
pip install -r requirements.txt
python app.py
# → http://localhost:5000  候補者フォーム
# → http://localhost:5000/admin  管理者ログイン
```

## Render.com へのデプロイ（無料）
1. https://render.com でアカウント作成
2. GitHubにこのフォルダをpush
3. Render Dashboard → "New" → "Web Service"
4. リポジトリを選択
5. Build Command: `pip install -r requirements.txt && python setup_fonts.py`
6. Start Command: `gunicorn app:app`
7. 環境変数を設定:
   - `SECRET_KEY`: 任意のランダム文字列
   - `ADMIN_PASSWORD`: 管理者パスワード（デフォルト: admin1234）
8. Deploy → 数分でURLが発行される

## 環境変数
| 変数名 | 説明 | デフォルト |
|--------|------|-----------|
| SECRET_KEY | セッション暗号化キー | change-me-in-production |
| ADMIN_PASSWORD | 管理者ログインパスワード | admin1234 |
