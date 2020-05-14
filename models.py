from datetime import datetime
from flask import abort, url_for, redirect, request, Markup
from flask_admin.contrib.sqla import ModelView
from flask_security import UserMixin, RoleMixin, current_user
from flask_security import SQLAlchemyUserDatastore
from flask_admin import expose

from app import db

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('admin.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id'))
)


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

    def __str__(self):
        return self.name


class Admin(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(70))
    last_name = db.Column(db.String(70))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    def __str__(self):
        return self.email


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_source_id = db.Column(db.String(256))
    source = db.Column(db.String(256))
    sessions = db.relationship('Session', backref='user', lazy='dynamic')
    requests = db.relationship('Request', backref='user', lazy='dynamic')
    states = db.relationship('State', backref='user', lazy='dynamic')
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return 'User {id}, source {source}'.format(
            id=self.id, source=self.source)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))
    request = db.Column(db.TEXT())
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return 'Request {id}, Text {request}'.format(
            id=self.id, request=self.request)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'request': self.request,
            'created_at': dump_datetime(self.created_at)
        }


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    requests = db.relationship('Request', backref='session', lazy='dynamic')
    confirmation_number = db.Column(db.String(256))
    department = db.Column(db.TEXT())
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return 'Session {id}, User ID {user_id}'.format(
            id=self.id, user_id=self.user_id)

    @property
    def serialize(self):
        """Return object data in easily serializable format"""
        return {
            'id': self.id,
            'confirmation_number': self.confirmation_number,
            'department': self.department,
            'created_at': dump_datetime(self.created_at),
            'requests': self.serialize_requests
        }

    @property
    def serialize_requests(self):
        """
        Return object's relations in easily serializable format.
        NB! Calls many2many's serialize property.
        """
        return [item.serialize for item in self.requests]


class State(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    state = db.Column(db.TEXT())
    last_lang = db.Column(db.TEXT())
    task_id = db.Column(db.TEXT(), default=None)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return 'State {id}, State {state}'.format(
            id=self.id, state=self.state)


class UserModelView(ModelView):
    can_export = True
    can_delete = False
    can_edit = False
    can_create = False
    page_size = 50
    can_view_details = True
    column_searchable_list = ['source']
    column_filters = ['source']

    column_formatters = dict(user_source_id=lambda v, c, m, p: Markup(
        u"<a href=" + str(m.id) + ">" + m.user_source_id + "</a>"))

    @expose('/details/<id>', methods=('GET', 'POST'))
    @expose('/<id>', methods=('GET', 'POST'))
    def list_view(self, id):
        """
            Custom create view.
        """
        user = User.query.filter_by(id=int(id)).first()
        if user is None:
            return redirect(url_for('security.login', next=request.url))
        sessions = Session.query.filter_by(user_id=user.id).order_by(
            Session.created_at.desc()
        ).all()
        serialized_sessions = [s.serialize for s in sessions]
        return self.render('analytics_index.html', user=user,
                           sessions=serialized_sessions)

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated
                )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect
         users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


class RequestModelView(ModelView):
    can_export = True
    can_delete = False
    can_edit = False
    can_create = False
    page_size = 50
    can_view_details = True
    column_searchable_list = ['user_id', 'request', 'session_id']
    column_filters = ['user_id', 'request', 'session_id']

    column_formatters = dict(user=lambda v, c, m, p: Markup(
        u"<a href=/admin/user/" + str(m.user_id) + ">" + str(
            m.user_id) + "</a>"))

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated
                )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect
        users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


class SessionModelView(ModelView):
    can_export = True
    can_delete = False
    can_edit = False
    can_create = False
    page_size = 50
    can_view_details = True
    column_searchable_list = ['department', 'confirmation_number']
    column_filters = ['department', 'confirmation_number']

    column_formatters = dict(user=lambda v, c, m, p: Markup(
        u"<a href=/admin/user/" + str(m.user_id) + ">" + str(m.user_id) + "</a>"))

    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated
                )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users
        when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return " ".join([value.strftime("%Y-%m-%d"), value.strftime("%H:%M:%S")])


user_datastore = SQLAlchemyUserDatastore(db, Admin, Role)
