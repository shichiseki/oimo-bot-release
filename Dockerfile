FROM python:3.9.13

# パッケージインストール
# libpq-devはpostgresqlライブラリ用
RUN apt update
RUN apt install -y locales ffmpeg libpq-dev

# ロケール設定
RUN locale-gen ja_JP.UTF-8
ENV TZ Asia/Tokyo
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja

# pythonライブラリインストール
WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install -r requirements.txt
COPY . .

CMD python discordbot.py