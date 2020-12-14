# !/usr/bin/env python3
# -*- coding: UTF-8 -*-
import asyncio
import json
import threading
import logging, subprocess
from configparser import ConfigParser
from time import time, sleep
from challenge import Challenge
from pyrogram import (Client, Filters, Message, User, InlineKeyboardButton,
                      InlineKeyboardMarkup, CallbackQuery, ChatPermissions)
from pyrogram.errors import ChatAdminRequired, ChannelPrivate, ChannelInvalid, MessageNotModified
from Timer import Timer

_app: Client = None
# _challenge_scheduler = sched.scheduler(time, sleep)
_current_challenges = dict()
_cch_lock = threading.Lock()
_config = dict()
'''
读 只 读 配 置
'''
cf = ConfigParser() #启用ConfigParser读取那些启动后即不会再被更改的数据，如BotToken等
cf.read("auth.ini")
_admin_user = cf.getint("bot", "admin")
_token = cf.get("bot", "token")
_api_id = cf.getint("bot", "api_id")
_api_hash = cf.get("bot", "api_hash")
_admin_user = cf.getint("bot", "admin")
_channel = cf.getint("bot", "channel")
logging.basicConfig(level=logging.INFO)
# 设置一下日志记录，能够在诸如 systemctl status captchabot 这样的地方获得详细输出。


def load_config():
    global _config
    with open("config.json", encoding="utf-8") as f:
        _config = json.load(f)


def save_config():
    with open("config.json", "w") as f:
        json.dump(_config, f, indent=4)


def _update(app):
    @app.on_message(Filters.command("reload") & Filters.private)
    async def reload_cfg(client: Client, message: Message):
        _me: User = await client.get_me()
        logging.info(message.text)
        if message.from_user.id == _admin_user:
            save_config()
            load_config()
            await message.reply("配置已成功重载。")
        else:
            logging.info("Permission denied, admin user in config is:"+_admin_user)
            pass

    @app.on_message(Filters.command("help") & Filters.group)
    async def helping_cmd(client: Client, message: Message):
        _me: User = await client.get_me()
        logging.info(message.text)
        await message.reply(_config["*"]["msg_self_introduction"],
                            disable_web_page_preview=True)
    @app.on_message(Filters.command("ping") & Filters.private)
    async def ping_command(client: Client, message: Message):
        await message.reply("poi~")

    @app.on_message(Filters.command("start") & Filters.private)
    async def start_command(client: Client, message: Message):
        await message.reply(_start_message)

    @app.on_message(Filters.command("leave") & Filters.private)
    async def leave_command(client: Client, message: Message):
        chat_id = message.text.split()[-1]
        if message.from_user.id == _admin_user:
            try:
                await client.send_message(int(chat_id),
                                          _config["msg_leave_msg"])
                await client.leave_chat(int(chat_id), True)
            except:
                await message.reply("指令出错了！可能是bot不在参数所在群里。")
            else:
                await message.reply("已离开群组: `" + chat_id + "`",
                                    parse_mode="Markdown")
                _me: User = await client.get_me()
                try:
                    await client.send_message(
                        int(_channel),
                        _config["msg_leave_group"].format(
                            botid=str(_me.id),
                            groupid=chat_id,
                        ),
                        parse_mode="Markdown")
                except Exception as e:
                    logging.error(str(e))
        else:
            pass

    @app.on_callback_query()
    async def challenge_callback(client: Client,
                                 callback_query: CallbackQuery):
        query_data = str(callback_query.data)
        query_id = callback_query.id
        chat_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        msg_id = callback_query.message.message_id
        chat_title = callback_query.message.chat.title
        user_name = callback_query.from_user.first_name
        group_config = _config.get(str(chat_id), _config["*"])
        if query_data in ["+", "-"]:
            admins = await client.get_chat_members(chat_id,
                                                   filter="administrators")
            if not any([
                    admin.user.id == user_id and
                (admin.status == "creator" or admin.can_restrict_members)
                    for admin in admins
            ]):
                await client.answer_callback_query(
                    query_id, group_config["msg_permission_denied"])
                return

            ch_id = "{chat}|{msg}".format(chat=chat_id, msg=msg_id)
            _cch_lock.acquire()
            # target: int = None
            challenge, target, timeout_event = _current_challenges.get(
                ch_id, (None, None, None))
            if ch_id in _current_challenges:
                # 预防异常
                del _current_challenges[ch_id]
            _cch_lock.release()
            timeout_event.stop()
            if query_data == "+":
                try:
                    await client.restrict_chat_member(
                        chat_id,
                        target,
                        permissions=ChatPermissions(
                            can_send_other_messages=True,
                            can_send_messages=True,
                            can_send_media_messages=True,
                            can_add_web_page_previews=True,
                            can_send_polls=True))
                except ChatAdminRequired:
                    await client.answer_callback_query(
                        query_id, group_config["msg_bot_no_permission"])
                    return

                await client.edit_message_text(
                    chat_id,
                    msg_id,
                    group_config["msg_approved"].format(user=user_name),
                    reply_markup=None,
                )
                _me: User = await client.get_me()
                try:
                    await client.send_message(
                        int(_channel),
                        _config["msg_passed_admin"].format(
                            botid=str(_me.id),
                            targetuser=str(target),
                            groupid=str(chat_id),
                            grouptitle=str(chat_title),
                        ),
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logging.error(str(e))
            else:
                try:
                    await client.kick_chat_member(chat_id, target)
                except ChatAdminRequired:
                    await client.answer_callback_query(
                        query_id, group_config["msg_bot_no_permission"])
                    return
                await client.edit_message_text(
                    chat_id,
                    msg_id,
                    group_config["msg_refused"].format(user=user_name),
                    reply_markup=None,
                )
                _me: User = await client.get_me()
                try:
                    await client.send_message(
                        int(_channel),
                        _config["msg_failed_admin"].format(
                            botid=str(_me.id),
                            targetuser=str(target),
                            groupid=str(chat_id),
                            grouptitle=str(chat_title),
                        ),
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logging.error(str(e))
            await client.answer_callback_query(query_id)
            return

        ch_id = "{chat}|{msg}".format(chat=chat_id, msg=msg_id)
        _cch_lock.acquire()
        challenge, target, timeout_event = _current_challenges.get(
            ch_id, (None, None, None))
        _cch_lock.release()
        if user_id != target:
            await client.answer_callback_query(
                query_id, group_config["msg_challenge_not_for_you"])
            return None
        timeout_event.stop()
        try:
            await client.restrict_chat_member(
                chat_id,
                target,
                permissions=ChatPermissions(can_send_other_messages=True,
                                            can_send_messages=True,
                                            can_send_media_messages=True,
                                            can_add_web_page_previews=True,
                                            can_send_polls=True))
        except ChatAdminRequired:
            pass

        correct = str(challenge.ans()) == query_data
        if correct:
            try:
                await client.edit_message_text(
                    chat_id,
                    msg_id,
                    group_config["msg_challenge_passed"],
                    reply_markup=None)
                _me: User = await client.get_me()
            except MessageNotModified as e:
                await client.send_message(int(_channel),
                                          'Bot 运行时发生异常: `' + str(e) + "`")
            try:
                await client.send_message(
                    int(_channel),
                    _config["msg_passed_answer"].format(
                        botid=str(_me.id),
                        targetuser=str(target),
                        groupid=str(chat_id),
                        grouptitle=str(chat_title),
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logging.error(str(e))
        else:
            if not group_config["use_strict_mode"]:
                await client.edit_message_text(
                    chat_id,
                    msg_id,
                    group_config["msg_challenge_mercy_passed"],
                    reply_markup=None,
                )
                _me: User = await client.get_me()
                try:
                    await client.send_message(
                        int(_channel),
                        _config["msg_passed_mercy"].format(
                            botid=str(_me.id),
                            targetuser=str(target),
                            groupid=str(chat_id),
                            grouptitle=str(chat_title),
                        ),
                        parse_mode="Markdown",
                    )
                except Exception as e:
                    logging.error(str(e))
            else:
                try:
                    await client.edit_message_text(
                        chat_id,
                        msg_id,
                        group_config["msg_challenge_failed"],
                        reply_markup=None,
                    )
                    # await client.restrict_chat_member(chat_id, target)
                    _me: User = await client.get_me()
                    try:
                        await client.send_message(
                            int(_channel),
                            _config["msg_failed_answer"].format(
                                botid=str(_me.id),
                                targetuser=str(target),
                                groupid=str(chat_id),
                                grouptitle=str(chat_title),
                            ),
                            parse_mode="Markdown",
                        )
                    except Exception as e:
                        logging.error(str(e))
                except ChatAdminRequired:
                    return

                if group_config["challenge_timeout_action"] == "ban":
                    await client.kick_chat_member(chat_id, user_id)
                elif group_config["challenge_timeout_action"] == "kick":
                    await client.kick_chat_member(chat_id, user_id)
                    await client.unban_chat_member(chat_id, user_id)
                elif group_config["challenge_timeout_action"] == "mute":
                    await client.restrict_chat_member(
                        chat_id,
                        user_id,
                        permissions=ChatPermissions(
                            can_send_other_messages=False,
                            can_send_messages=False,
                            can_send_media_messages=False,
                            can_add_web_page_previews=False,
                            can_send_polls=False))

                else:
                    pass

                if group_config["delete_failed_challenge"]:
                    Timer(
                        client.delete_messages(chat_id, msg_id),
                        group_config["delete_failed_challenge_interval"],
                    )
        if group_config["delete_passed_challenge"]:
            Timer(
                client.delete_messages(chat_id, msg_id),
                group_config["delete_passed_challenge_interval"],
            )

    @app.on_message(Filters.new_chat_members)
    async def challenge_user(client: Client, message: Message):
        target = message.new_chat_members[0]
        if message.from_user.id != target.id:
            if target.is_self:
                group_config = _config.get(str(message.chat.id), _config["*"])
                try:
                    await client.send_message(
                        message.chat.id, group_config["msg_self_introduction"])
                    _me: User = await client.get_me()
                    try:
                        await client.send_message(
                            int(_channel),
                            _config["msg_into_group"].format(
                                botid=str(_me.id),
                                groupid=str(message.chat.id),
                                grouptitle=str(message.chat.title),
                            ),
                            parse_mode="Markdown",
                        )
                    except Exception as e:
                        logging.error(str(e))
                except ChannelPrivate:
                    return
            return
        try:
            await client.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=target.id,
                permissions=ChatPermissions(can_send_other_messages=False,
                                            can_send_messages=False,
                                            can_send_media_messages=False,
                                            can_add_web_page_previews=False,
                                            can_send_polls=False))
        except ChatAdminRequired:
            return
        group_config = _config.get(str(message.chat.id), _config["*"])
        challenge = Challenge()

        def generate_challenge_button(e):
            choices = []
            answers = []
            for c in e.choices():
                answers.append(
                    InlineKeyboardButton(str(c),
                                         callback_data=bytes(
                                             str(c), encoding="utf-8")))
            choices.append(answers)
            return choices + [[
                InlineKeyboardButton(group_config["msg_approve_manually"],
                                     callback_data=b"+"),
                InlineKeyboardButton(group_config["msg_refuse_manually"],
                                     callback_data=b"-"),
            ]]

        timeout = group_config["challenge_timeout"]
        reply_message = await client.send_message(
            message.chat.id,
            group_config["msg_challenge"].format(target=target.first_name,
                                                 target_id=target.id,
                                                 timeout=timeout,
                                                 challenge=challenge.qus()),
            reply_to_message_id=message.message_id,
            reply_markup=InlineKeyboardMarkup(
                generate_challenge_button(challenge)),
        )
        _me: User = await client.get_me()
        chat_id = message.chat.id
        chat_title = message.chat.title
        target = message.from_user.id
        timeout_event = Timer(
            challenge_timeout(client, message.chat.id, message.from_user.id,
                              reply_message.message_id),
            timeout=group_config["challenge_timeout"],
        )
        _cch_lock.acquire()
        _current_challenges["{chat}|{msg}".format(
            chat=message.chat.id,
            msg=reply_message.message_id)] = (challenge, message.from_user.id,
                                              timeout_event)
        _cch_lock.release()

    async def challenge_timeout(client: Client, chat_id, from_id, reply_id):
        global _current_challenges
        _me: User = await client.get_me()
        group_config = _config.get(str(chat_id), _config["*"])

        _cch_lock.acquire()
        del _current_challenges["{chat}|{msg}".format(chat=chat_id,
                                                      msg=reply_id)]
        _cch_lock.release()

        # TODO try catch
        await client.edit_message_text(
            chat_id=chat_id,
            message_id=reply_id,
            text=group_config["msg_challenge_failed"],
            reply_markup=None,
        )
        await client.send_message(chat_id=_channel,
                                  text=_config["msg_failed_timeout"].format(
                                      botid=str(_me.id),
                                      targetuser=str(from_id),
                                      groupid=str(chat_id)))
        if group_config["challenge_timeout_action"] == "ban":
            await client.kick_chat_member(chat_id, from_id)
        elif group_config["challenge_timeout_action"] == "kick":
            await client.kick_chat_member(chat_id, from_id)
            await client.unban_chat_member(chat_id, from_id)
        else:
            pass

        if group_config["delete_failed_challenge"]:
            Timer(
                client.delete_messages(chat_id, reply_id),
                group_config["delete_failed_challenge_interval"],
            )


def _main():
    global _app, _channel, _start_message, _config
    load_config()
    _start_message = _config["msg_start_message"]
    _proxy_ip = _config["proxy_addr"].strip()
    _proxy_port = _config["proxy_port"].strip()
    if _proxy_ip and _proxy_port:
        _app = Client("bot",
                      bot_token=_token,
                      api_id=_api_id,
                      api_hash=_api_hash,
                      proxy=dict(hostname=_proxy_ip, port=int(_proxy_port)))
    else:
        _app = Client("bot",
                      bot_token=_token,
                      api_id=_api_id,
                      api_hash=_api_hash)
    try:
        _update(_app)
        _app.run()
    except KeyboardInterrupt:
        quit()
    except Exception as e:
        logging.error(e)
        _main()


if __name__ == "__main__":
    _main()
