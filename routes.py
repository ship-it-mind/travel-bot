from flask import request, render_template, redirect
import telegram
from core.dialog.manager import DialogManger
from extensions import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_ENDPOINT_URL,
    FB_VERIFY_TOKEN,
    LOGGER
)
from connector.telegram.bot import Bot as Telegram_Bot
from app import app

dialog_manager = DialogManger()
telegram_bot = Telegram_Bot(
    access_token=TELEGRAM_BOT_TOKEN
)


@app.route('/')
def index():
    return redirect('/admin')


@app.route('/{}'.format(TELEGRAM_BOT_TOKEN), methods=['POST'])
def respond():
    # retrieve the message in JSON and then transform it to Telegram object
    update = telegram.Update.de_json(request.get_json(force=True),
                                     telegram_bot)

    if update.message is not None:

        chat_id = update.message.chat.id
        LOGGER.info("got chat :" + str(update.message.chat))
        # Telegram understands UTF-8, so encode text for unicode compatibility
        message = update.message.text
        # for debugging purposes only
        LOGGER.info("got text message :" + message)
        dialog_manager.process_message(
            message,
            chat_id,
            'telegram',
            update.message,
            update.message.from_user.language_code
        )

        return 'ok'
    elif update.callback_query is not None:
        chat_id = update.callback_query.message.chat.id

        # Telegram understands UTF-8, so encode text for unicode compatibility
        message = update.callback_query.data
        # for debugging purposes only
        LOGGER.info("got text message :" + message)
        dialog_manager.process_message(
            message,
            chat_id,
            'telegram',
            update.callback_query.message,
            update.callback_query.from_user.language_code,
        )

        return 'ok'


@app.route('/set-telegram-webhook', methods=['GET', 'POST'])
def set_webhook():
    # we use the bot object to link the bot to our app which live
    # in the link provided by URL
    s = telegram_bot.bot.setWebhook('{URL}{HOOK}'.format(
        URL=TELEGRAM_ENDPOINT_URL,
        HOOK=TELEGRAM_BOT_TOKEN)
    )
    # something to let us know things work
    if s:
        return "Webhook setup ok"
    else:
        return "Webhook setup failed"


@app.route("/facebook-webhook", methods=['GET', 'POST'])
def fb_webhook():
    if request.method == 'GET':
        token = request.args.get("hub.verify_token")
        if token == FB_VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        else:
            return 'Invalid verification token'

    if request.method == 'POST':
        output = request.get_json()
        LOGGER.info(output)
        for event in output['entry']:
            messaging = event['messaging']
            for x in messaging:
                LOGGER.info(x)
                if x.get('message'):
                    recipient_id = str(x['sender']['id'])
                    if x['message'].get('text'):
                        message = x['message']['text']
                        dialog_manager.process_message(
                            message,
                            recipient_id,
                            'facebook')

                elif x.get('postback'):
                    recipient_id = str(x['sender']['id'])
                    if x['postback'].get('title'):
                        message = x['postback']['title']
                        dialog_manager.process_message(message,
                                                       recipient_id,
                                                       'facebook')
        return "Success"
