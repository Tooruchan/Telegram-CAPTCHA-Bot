# Telegram-CAPTCHA-bot

一个用于验证新成员是不是真人的bot。

本仓库已停止更新，请移步至新仓库：https://github.com/Tooruchan/Telegram-CAPTCHA-bot-pyrogram

[![GNU Public License Affero 3.0](https://img.shields.io/badge/license-AGPL3.0-%23373737.svg)](https://www.gnu.org/licenses/agpl-3.0.en.html) [![Python 3.6](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org) [![Pyrogram](https://img.shields.io/badge/Pyrogram-asyncio-green.svg)](https://github.com/pyrogram/pyrogram/)

A bot running on Telegram which will send CAPTCHA to verify if the new member is a human.

基于[原始项目](https://github.com/lziad/Telegram-CAPTCHA-bot)重制  

Remaked and forked based on [Original Repository](https://github.com/lziad/Telegram-CAPTCHA-bot)

修改者：Telegram [@Yoshida_Yuuko](https://t.me/Yoshida_Yuuko) Rsplwe

Bot实例: [@toorucaptchabot](https://t.me/toorucaptchabot)
## 一些简单的Q&A

**Q:** 请问这个Bot是否会窃听群组消息？

**A:** 根据 [Telegram 官方文档](https://core.telegram.org/bots#privacy-mode)，工作在隐私模式下的非管理员 bot 只能获取下列几种消息：

       - 以"/"斜杠开头的命令
       
       - 对 bot 消息的回复
       
       - 服务消息（即进群和退群消息等，这也是本 Bot 工作的原理）
       
       - 当 bot 是某一频道的管理员时，从这个频道转发出来的消息

然而，对于设置为群组管理员的 bot，即便是设置了隐私模式，Telegram 服务器仍然会使 bot 接收到一切消息（除了因为限制，bot 本身完全无法收到的消息）。但是请您放心，我们的现有部署所运行的代码只会处理上文中提到的“服务消息”，并不会对您群组内的隐私安全造成威胁。

如果你对我们现有的部署不放心的话，可以自行 clone 本仓库代码并在自己的服务器/Docker 容器上自行部署。
       
~~如果你并没有编程基础，或者并没有详细阅读本项目的代码，而对本项目的安全性提出质疑，我们将会不予理会。~~
## 原理

本 Bot 通过读取 Telegram API 中返回的入群消息来识别新用户入群，并生成一道随机问题对用户进行验证，非严格模式只要有回答问题就通过；严格模式下回答错误将会被移除或者封禁，这个验证的效果目前无法绕过具有人工操作的广告机器人，但是可以对外语（如阿拉伯语和波斯语）类骚扰用户起到一定的拦截作用。

Telegram Bot API 使用了基于 MTProto 框架的 pyrogram，多线程使用了 asyncio。

## 安装与使用
**由于 Bot 使用了 Python 3.6 的 [变量类型标注](https://docs.python.org/zh-cn/3/library/typing.html) 这一特性，在低于 Python 3.6 的版本上会出现 SyntaxError，因此源码只能在 Python 3.6+ 上运行!**  
1. 请先向 [@BotFather](https://t.me/botfather) 申请一个 Bot API Token  
> 你申请到的机器人会在你的 Telegram 账号所在数据中心上运行（即申请机器人的账号A位于 DC 5 (新加坡)，则 A 申请到的机器人也将会在 DC5 上运行)
2. 在 [Obtaining Telegram API ID](https://core.telegram.org/api/obtaining_api_id) 申请 API ID 与 API Hash
3. 在服务器上安装 pyrogram 以及 tgcrypto（以 Ubuntu 18.04 LTS 为例）: 
```
# 若未安装pip3，请先安装 python3-pip
apt install python3-pip
pip3 install -U tgcrypto pyrogram configparser
# 项目当前已适配并兼容最新的 pyrogram v1.1.3（自带 asyncio 支持），直接通过 Pypi 安装即可。
git clone https://github.com/Tooruchan/Telegram-CAPTCHA-bot 
cd Telegram-CAPTCHA-bot
```

4. 将项目文件夹中 auth.ini 里的 token 字段（与等号间存在一个空格）修改为你在 [@BotFather](https://t.me/botfather) 获取到的 API Token，api_hash 和 api_id 修改为你在步骤2中获得的两串内容，其中 API ID 为数字，而 API Hash 为一组字符，你也可以对 config.json 里的内容酌情修改。

有关填写字段说明:

`channel`: Bot 日志记录频道，未填写将会导致无法正常工作（这是一个 bug，等待修复）。

`admin`: 管理用户，不填写则`/leave`和`/reload`指令无效。

5. 使用 `python3 main.py` 直接运行这个 bot,或者在 `/etc/systemd/system/ `下新建一个 .service 文件，使用 systemd 控制这个bot的运行，配置文件示例请参考本项目目录下的 `example.service` 文件进行修改。

6. 将本 bot 加入一个群组，并给予封禁用户的权限，即可开始使用

## 在多个群组（10个以上等）部署本Bot的提示

~~由于一个已知无解的严重 Bug， Bot 在运行一周至13天左右的时间可能会由于线程冲突导致整个 Bot 死掉，如果需要在多个（10个以上）的群组内部署本 Bot 请考虑在crontab等地方设置定期重启。~~

现在的分支加入了一遇到异常就会自动重启的设定，Bot 在正常运行情况下应该是不会卡死了。

## 日志
在安装了 systemd ，且已经在 /etc/systemd/system 下部署了服务的 Linux 操作系统环境下，请使用命令：
```bash
journalctl -u captchabot.service 
# 这里的 captchabot.service 请自行更名为你在服务器上部署的服务名
```

## 项目实例
[@toorucaptchabot](https://t.me/toorucaptchabot)

本项目在 PyPy 3.6 和 pyrogram v0.16.0.asyncio 上测试通过  

[@AffyunWatchCatBot](https://t.me/AffyunWatchCatBot)

(环境为 Python 3.7.3 和 pyrogram v0.12.0.asyncio)

[@JustCaptchaBot](https://t.me/JustCaptchaBot)

(环境为 PyPy 3.6 + pyrogram v0.13.0.asyncio)

## 开源协议
本项目使用 GNU Affero 通用公共许可证 3.0 开源
