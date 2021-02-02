#!/bin/bash

check_dep() {
	if [ $(python -m pip check) ]; then
		source venv/bin/activate
		pip freeze > requirements.txt
		pip install -r requirements.txt --upgrade
		pip install -U pyrogram-asyncio.zip
		pip install --upgrade tgcrypto configparser
	fi
	if [ $(pip list --disable-pip-version-check | grep -E "^tgcrypto") ]; then
		source venv/bin/activate; pip install --upgrade tgcrypto
	fi
	if [ $(pip list --disable-pip-version-check | grep -E "^configparser") ]; then
		source venv/bin/activate; pip install --upgrade configparser
	fi
	if [ $(pip list --disable-pip-version-check | grep -E "^pyrogram") ]; then
		source venv/bin/activate; pip install --upgrade pyrogram
	fi
}

main() {
	cd /tg-captcha/workdir
	check_dep
	if [[ ! -f auth.ini ]] || [[ ! -f config.json ]]; then
		echo ""
		exit(1)
	fi
	git pull
	/tg-captcha/workdir/venv/bin/python /tg-captcha/workdir/main.py
}

main
