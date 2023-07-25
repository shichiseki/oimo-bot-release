# おいもbot
バトオペ用Discordbotのお試し版です。
# 使い方
## 招待
[こちら](https://discord.com/api/oauth2/authorize?client_id=1114472393247821926&permissions=2167408640&scope=bot)からbotを自分のサーバーに招待します。
## 送信先設定
自分のサーバーに招待すると設定メッセージが一番上のテキストチャンネルに送信されます。


## 各種ファイル情報

### discordbot.py
PythonによるDiscordBotのアプリケーションファイルです。

### cogs
#### eventcog.py
各種イベント(ボイスチャンネル入室時、メッセージが送信時)での処理を記述したファイルです。
#### maincog.py
通常コマンドのファイルです。

### requirements.txt
使用しているPythonのライブラリ情報の設定ファイルです。

### .github/workflows/flake8.yaml
GitHub Actions による自動構文チェックの設定ファイルです。

### .github/workflows/fly.io_deploy.yml
fly.ioのデプロイ用ファイルです。

### LICENSE
このリポジトリのコードの権利情報です。MITライセンスの範囲でご自由にご利用ください。

### README.md
このドキュメントです。

# 開発用メモ
## TODO
- 説明書作成
- グローバルコマンド
- Dockerfile

## DONE
- チーム分け、読み上げ以外の機能をオミット
- チーム分けのレート登録を辞書に
- - レート登録を辞書に変更したことに伴うチーム分けの処理変更
- ボイスチャンネル入退室メッセージ送信チャンネルをDBに保存する
- 設定viewの説明emb作成
- botにconn作成
- 読み上げをGTTSに
- botにチャンネルdict作成
- DB処理

## メモ
- ~~Modalでのレート値の保存方法について検討。他の人のModal見たけど、やっぱりクラス渡して保存してたので、レーティング登録view上で保存することにする setattrを試す~~ ← 結局Modal内のinputを参照する必要があるし辞書渡すことにした Modalをユーザーごとに保持して値が上書きされてしまうの防ぐ(ユーザー数が多くなったとき大丈夫？)


## requirementsの書き方

### インストール
```
pip install -r requirements.txt
```
### 書き出し
```
pip freeze > requirements.txt
```

# Emoji
 ==================== Emojis ====================  
🌱  :seedling: 初めてのコミット（Initial Commit）  
🔖  :bookmark: バージョンタグ（Version Tag）  
✨  :sparkles: 新機能（New Feature）  
🐛  :bug: バグ修正（Bugfix）  
♻️  :recycle: リファクタリング(Refactoring)  
📚  :books: ドキュメント（Documentation）  
🎨  :art: デザインUI/UX(Accessibility)  
🐎  :horse: パフォーマンス（Performance）  
🔧  :wrench: ツール（Tooling）  
🚨  :rotating_light: テスト（Tests）  
💩  :hankey: 非推奨追加（Deprecation）  
🗑️  :wastebasket: 削除（Removal）  
🚧  :construction: WIP(Work In Progress)
