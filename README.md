# おいもbot
バトオペ用Discordbotのお試し版です。

# 機能
## ボイスチャンネル入退室ログ
ボイスチャンネル入退室時に任意のチャンネルにメッセージを送信します。
![](./docs/images/ボイスチャンネルログ.png)
## 自動チーム分けおよび自動ボイスチャンネル移動
レーティング値を登録してレーティングの差がないようなチームに分けたり、ランダムなチームに分けたりすることができます。

<img src=./docs/images/レーティング登録.png width=320> <img src=./docs/images/チーム分け.png width=320>
## 読み上げ
[gTTS(Google Text-to-Speech)](https://github.com/pndurette/gTTS)を用いて、テキストチャンネルに送信されたメッセージをボイスチャンネル内で読み上げます。

# 使い方
## 招待
[こちら](https://discord.com/api/oauth2/authorize?client_id=1114472393247821926&permissions=2167408640&scope=bot)からbotを自分のサーバーに招待します。
## 送信先設定
自分のサーバーに招待すると設定メッセージが一番上のテキストチャンネルに送信されます。

# 注意事項

# 説明

## discordbot.py
PythonによるDiscordBotのアプリケーションファイルです。

## cogs
## eventcog.py
各種イベント(ボイスチャンネル入室時、メッセージが送信時)での処理を記述したファイルです。
## maincog.py
通常コマンドのファイルです。

## requirements.txt
使用しているPythonのライブラリ情報の設定ファイルです。

## .github/workflows/flake8.yaml
GitHub Actions による自動構文チェックの設定ファイルです。

## .github/workflows/fly.io_deploy.yml
fly.ioのデプロイ用ファイルです。

## LICENSE
このリポジトリのコードの権利情報です。MITライセンスの範囲でご自由にご利用ください。

## README.md
このドキュメントです。