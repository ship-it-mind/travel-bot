from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from celery import Celery
from flask_admin import Admin
from flask_security import Security
from flask_admin import helpers as admin_helpers
from flask_mail import Mail

from config import Config, mail_settings

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)
admin = Admin(app, name='Destinia', template_mode='bootstrap3')
app.config.update(mail_settings)
mail = Mail(app)

from routes import *
from models import *


admin.add_view(UserModelView(User, db.session))
admin.add_view(SessionModelView(Session, db.session))
admin.add_view(RequestModelView(Request, db.session))


if __name__ == '__main__':
    security = Security(app, user_datastore)

    @security.context_processor
    def security_context_processor():
        return dict(
            admin_base_template=admin.base_template,
            admin_view=admin.index_view,
            h=admin_helpers,
            get_url=url_for
        )
    app.run('0.0.0.0', 88)
