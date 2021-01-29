FROM python:3-alpine
RUN apk add \
    git \
    gcc \
    musl-dev
RUN mkdir -p /tg-captcha/workdir
RUN git clone -b master https://github.com/Tooruchan/Telegram-CAPTCHA-Bot.git /tg-captcha/workdir
WORKDIR /tg-captcha/workdir
RUN python -m pip install virtualenv
RUN python -m virtualenv venv
RUN source venv/bin/activate; pip install -U pyrogram-asyncio.zip; pip install --upgrade tgcrypto configparser
CMD ["sh","docker-run.sh"]
