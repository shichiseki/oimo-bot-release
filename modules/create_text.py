import re
from discord import Message


def remove_custom_emoji(send_text):
    # カスタム絵文字のパターン
    pattern = r"<:[a-zA-Z0-9_]+:[0-9]+>"
    return re.sub(pattern, "", send_text)


def remove_url(send_text):
    # URLパターン
    pattern = r"https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    if re.search(pattern, send_text):
        return "URLが送信されました " + re.sub(pattern, "", send_text)

    else:
        return send_text


def remove_under_bar(send_text):
    # アンダーバーパターン
    pattern = r"[*_]"
    return re.sub(pattern, "", send_text)


def is_image(message: Message):
    for att in message.attachments:
        if att.content_type.startswith("image"):
            return True

    else:
        return False


def create_text(message: Message, word_dic: dict, words_limit=30):
    # 画像が送信されたとき
    if is_image(message):
        return "画像が送信されました。"

    # メッセージテキスト取得
    send_text = message.clean_content

    # 辞書適用
    for key, value in sorted(word_dic, reverse=True):
        send_text = send_text.replace(key, value)

    # 読み上げできる形式に加工
    send_text = remove_custom_emoji(send_text)
    send_text = remove_under_bar(send_text)
    send_text = remove_url(send_text)

    return send_text[:words_limit]
