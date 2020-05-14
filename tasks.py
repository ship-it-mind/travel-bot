from app import celery, mail, app
from connector.facebook.bot import Bot as FBot
from connector.telegram.bot import Bot as TelegramBot
from flask import render_template
from flask_mail import Message
from extensions import (FB_PAGE_ACCESS_TOKEN,
                        TELEGRAM_BOT_TOKEN
                        )

fb_bot = FBot(
    access_token=FB_PAGE_ACCESS_TOKEN
)
telegram_bot = TelegramBot(
    access_token=TELEGRAM_BOT_TOKEN
)


@celery.task
def send_ask_question_solved(recipient_id, language, channel):
    if language == 'en':
        if channel == 'facebook':
            fb_bot.send_quick_replies(
                recipient_id=recipient_id,
                message="Have been your question solved?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'Yes',
                        "payload": 'yes'
                    },
                    {
                        "content_type": 'text',
                        "title": 'No',
                        "payload": 'no'
                    }
                ]
            )
        elif channel == 'telegram':
            telegram_bot.send_keyboard_message(
                recipient_id=recipient_id,
                message="Have been your question solved?",
                buttons=[
                    "Yes",
                    "No"
                ]
            )
    elif language == 'es':
        if channel == 'facebook':
            fb_bot.send_quick_replies(
                recipient_id=recipient_id,
                message="¿Has resuelto tu duda?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'Si',
                        "payload": 'yes'
                    },
                    {
                        "content_type": 'text',
                        "title": 'No',
                        "payload": 'no'
                    }
                ]
            )
        elif channel == 'telegram':
            telegram_bot.send_keyboard_message(
                recipient_id=recipient_id,
                message="¿Has resuelto tu duda?",
                buttons=[
                    "Si",
                    "No"
                ]
            )


@celery.task
def send_report_mail(recipient_id, language, channel, session, requests, name):
    with app.app_context():
        msg = Message(subject="Report - {}".format(name),
                      sender='destinachatbot@tqniatlab.com',
                      recipients=['destiniachatbot@tqniat.com'],
                      html=render_template('email/mail_temp.html',
                                           session=session,
                                           requests=requests,
                                           channel=channel,
                                           name=name))
        mail.send(msg)
