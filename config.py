import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

dot_env_path = os.path.join(os.path.dirname(__file__),
                            os.path.join(os.getcwd(), '.env'))
load_dotenv(dot_env_path)


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.getenv('MySQL_CON_LINE')
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND')
    FLASK_ADMIN_SWATCH = os.getenv('FLASK_ADMIN_SWATCH')
    SECRET_KEY = os.getenv('SECRET_KEY')
    SECURITY_LOGIN_URL = os.getenv('SECURITY_LOGIN_URL')
    SECURITY_LOGOUT_URL = os.getenv('SECURITY_LOGOUT_URL')
    SECURITY_REGISTER_URL = os.getenv('SECURITY_REGISTER_URL')
    SECURITY_POST_LOGIN_VIEW = os.getenv('SECURITY_POST_LOGOUT_VIEW')
    SECURITY_POST_REGISTER_VIEW = os.getenv('SECURITY_POST_REGISTER_VIEW')
    SECURITY_REGISTERABLE = os.getenv('SECURITY_REGISTERABLE')
    SECURITY_SEND_REGISTER_EMAIL = os.getenv('SECURITY_SEND_REGISTER_EMAIL')
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_BOT_NAME = os.getenv('TELEGRAM_BOT_NAME')
    TELEGRAM_ENDPOINT_URL = os.getenv('TELEGRAM_ENDPOINT_URL')
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT'))
    MAIL_USE_TLS = bool(os.getenv('MAIL_USE_TLS'))
    MAIL_USE_SSL = bool(os.getenv('MAIL_USE_SSL'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')


mail_settings = {
    "MAIL_SERVER": 'smtp.mailgun.org',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": 'destiniachatbot@mailgun.tqniatlab.com',
    "MAIL_PASSWORD": 'e44e3799f0f266655429ab3d6decf33a-a9919d1f-74d6a6a0'
}