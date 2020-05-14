from celery import current_app

from models import User, Request, Session, State, db
from core.nlp.engine import NLPEngine
from connector.telegram.bot import Bot as Telegram_Bot
from connector.facebook.bot import Bot as FBot
from extensions import (
    FB_PAGE_ACCESS_TOKEN,
    TELEGRAM_BOT_TOKEN,
    LOGGER
)
from tasks import (
    send_ask_question_solved,
    send_report_mail
)


class DialogManger:
    def __init__(self):
        self.engine = NLPEngine()
        self.fb_bot = FBot(
            access_token=FB_PAGE_ACCESS_TOKEN
        )
        self.telegram_bot = Telegram_Bot(
            access_token=TELEGRAM_BOT_TOKEN
        )

    def process_message(self, message, source_user_id,
                        channel, full_obj=None, telegram_language_code='es'):
        user = self.get_user(
            user_id=source_user_id,
            channel=channel
        )
        task_id = self.get_user_task_id(
            user_id=user.id
        )
        if task_id is not None:
            current_app.control.revoke(task_id, terminate=True)
            self.set_user_task_id(
                user_id=user.id,
                task_id=None
            )
        user_state = self.get_user_state(user.id)
        user_last_lang = self.get_user_last_lang(user.id)
        if user_state == 'IDLE':
            if channel == 'facebook':
                current_locale = self.fb_bot.get_user_info(
                    recipient_id=source_user_id,
                    fields=['locale']
                ).get('locale')

                self.route_fb_prediction(
                    user_id=user.id,
                    recipient_id=source_user_id,
                    message=message,
                    user_last_lang=user_last_lang,
                    current_locale=current_locale
                )
            elif channel == 'telegram':
                self.route_telegram_prediction(
                    user_id=user.id,
                    recipient_id=source_user_id,
                    message=message,
                    full_obj=full_obj,
                    user_last_lang=user_last_lang,
                    current_locale=telegram_language_code
                )
        elif user_state == 'WAIT_FIRST_REQUEST':
            self.initiate_create_request(
                recipient_id=source_user_id,
                channel=channel,
                message=message
            )
            if channel == 'facebook':
                self.fb_bot.send_anything_else(
                    recipient_id=source_user_id,
                    language=user_last_lang
                )
            elif channel == 'telegram':
                self.telegram_bot.send_anything_else(
                    recipient_id=source_user_id,
                    language=user_last_lang
                )

        elif user_state == 'WAIT_CONFIRMATION_NUMBER':
            self.initiate_add_confirmation_number(
                recipient_id=source_user_id,
                channel=channel,
                message=message
            )
            if channel == 'facebook':
                self.fb_bot.send_ask_another_request(
                    recipient_id=source_user_id,
                    language=user_last_lang
                )
            elif channel == 'telegram':
                self.telegram_bot.send_ask_another_request(
                    recipient_id=source_user_id,
                    language=user_last_lang
                )
            self.set_user_state(user.id, "IDLE")
        elif user_state == 'WAIT_SECOND_REQUEST':
            self.initiate_create_request(
                recipient_id=source_user_id,
                channel=channel,
                message=message
            )
            if channel == 'facebook':
                self.fb_bot.send_anything_else(
                    recipient_id=source_user_id,
                    language=user_last_lang
                )
            elif channel == 'telegram':
                self.telegram_bot.send_anything_else(
                    recipient_id=source_user_id,
                    language=user_last_lang
                )

    def get_user(self, user_id, channel):
        user = User.query.filter_by(user_source_id=int(user_id)).first()
        LOGGER.info(user_id)
        LOGGER.info(user)
        if user is None:
            user = self.create_user(
                source_user_id=user_id,
                channel=channel
            )
        return user

    @staticmethod
    def get_user_state(user_id):
        state = State.query.filter_by(user_id=user_id).first()
        if state is not None:
            return state.state

    @staticmethod
    def get_user_last_lang(user_id):
        state = State.query.filter_by(user_id=user_id).first()
        if state is not None:
            return state.last_lang

    @staticmethod
    def get_user_task_id(user_id):
        state = State.query.filter_by(user_id=user_id).first()
        if state is not None:
            return state.task_id

    @staticmethod
    def set_user_state(user_id, new_state):
        state = State.query.filter_by(user_id=user_id).first()
        if state is not None:
            state.state = new_state
            db.session.commit()
            return state

    @staticmethod
    def set_user_last_lang(user_id, new_lang):
        state = State.query.filter_by(user_id=user_id).first()
        if state is not None:
            state.last_lang = new_lang
            db.session.commit()
            return state

    @staticmethod
    def set_user_task_id(user_id, task_id):
        state = State.query.filter_by(user_id=user_id).first()
        if state is not None:
            state.task_id = task_id
            db.session.commit()
            return state

    def create_user(self, source_user_id, channel):
        user = User(user_source_id=source_user_id, source=channel)
        db.session.add(user)
        db.session.commit()
        self.create_user_state(
            user=user
        )
        return user

    def initiate_wait_first_request_session(self,
                                            recipient_id,
                                            channel,
                                            department):
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        self.create_user_session(
            user=user,
            department=department
        )
        self.set_user_state(user.id, "WAIT_FIRST_REQUEST")

    def initiate_wait_request_session(self,
                                      recipient_id,
                                      channel):
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        self.set_user_state(user.id, "WAIT_FIRST_REQUEST")

    def initiate_wait_second_request_session(self, recipient_id, channel):
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        self.set_user_state(user.id, "WAIT_SECOND_REQUEST")

    def initiate_wait_confirmation_number_session(self, recipient_id, channel):
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        self.set_user_state(user.id, "WAIT_CONFIRMATION_NUMBER")

    def initiate_create_request(self, recipient_id, channel, message):
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        session = self.get_user_latest_session(
            user_id=user.id
        )
        self.create_user_request(
            user=user,
            session=session,
            request=message
        )
        self.set_user_state(user.id, "IDLE")

    def initiate_add_confirmation_number(self, recipient_id, channel, message):
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        session = self.get_user_latest_session(
            user_id=user.id
        )
        self.update_session_confirmation_number(
            session=session,
            message=message
        )
        self.set_user_state(user.id, "IDLE")

    def initiate_have_question(self, recipient_id, language, channel):
        task = send_ask_question_solved.apply_async(
            args=[
                recipient_id,
                language,
                channel
            ],
            countdown=60
        )
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        self.set_user_task_id(
            user_id=user.id,
            task_id=task.task_id
        )

    def initiate_send_report(self, recipient_id,
                             language, channel, full_obj=None):
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        session = self.get_user_latest_session(
            user_id=user.id
        ).serialize
        LOGGER.info("Pre Send Mail")
        user_info = {}
        if channel == 'facebook':
            user_info = self.fb_bot.get_user_info(
                recipient_id=recipient_id,
                fields=['name']
            )
        elif channel == 'telegram':
            user_info = self.telegram_bot.get_user_info(
                full_obj=full_obj
            )
        name = user_info.get('name')
        if session is not None:
            LOGGER.info("Send Mail")
            send_report_mail.apply_async(
                args=[
                    recipient_id,
                    language,
                    channel,
                    session,
                    session['requests'],
                    name
                ],
                countdown=1
            )

    def initiate_cancel(self, recipient_id, language, channel):
        task = send_ask_question_solved.apply_async(
            args=[
                recipient_id,
                language,
                channel
            ],
            countdown=60
        )
        user = self.get_user(
            user_id=recipient_id,
            channel=channel
        )
        self.set_user_task_id(
            user_id=user.id,
            task_id=task.task_id
        )

    @staticmethod
    def create_user_request(user, session, request):
        request = Request(request=request, user=user, session=session)
        db.session.add(request)
        db.session.commit()
        return request

    @staticmethod
    def update_session_confirmation_number(session, message):
        session.confirmation_number = message
        db.session.commit()
        return session

    @staticmethod
    def create_user_state(user):
        state = State(state='IDLE', user=user)
        db.session.add(state)
        db.session.commit()
        return state

    @staticmethod
    def create_user_session(user, department):
        session = Session(
            confirmation_number=None,
            department=department,
            user=user
        )
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def get_user_latest_session(user_id):
        session = Session.query.filter_by(
            user_id=user_id
        ).order_by(
            Session.created_at.desc()
        ).first()
        if session is not None:
            return session

    def route_fb_prediction(self, user_id, recipient_id,
                            message, user_last_lang, current_locale):
        if message == 'Get Started':
            LOGGER.info("Get Started Flow")
            intent = 'greeting'
            LOGGER.info(current_locale)
            if current_locale.startswith("en"):
                language = "en"
            elif current_locale.startswith("es"):
                language = "es"
            else:
                language = "es"
        else:
            intent, language = self.engine.predict(
                user_id=user_id,
                message=message,
                last_lang=user_last_lang,
                current_locale=current_locale
            )
        self.set_user_last_lang(
            user_id=user_id,
            new_lang=language
        )
        LOGGER.info(intent)
        if intent == 'Default Fallback Intent':
            self.fb_bot.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='facebook',
                language=language
            )
            self.fb_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='facebook',
                department="Flight"
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight':
            self.fb_bot.send_manage_booking_options(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='facebook',
                language=language
            )
            self.fb_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='facebook',
                department="Flight"
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='facebook',
                language=language
            )
            self.fb_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='facebook',
                department="Flight"
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question':
            self.fb_bot.send_have_flight_question(
                recipient_id=recipient_id,
                language=language
            )
            if language == 'en':
                self.initiate_have_question(
                    recipient_id=recipient_id,
                    language=language,
                    channel='facebook'
                )
        elif intent == 'manage_booking.flight.question - equipaje':
            self.fb_bot.send_have_question_equipaje(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - checkin':
            self.fb_bot.send_have_question_checkin(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - otras':
            self.fb_bot.send_have_question_otras(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_have_question(
                recipient_id=recipient_id,
                language=language,
                channel='facebook'
            )
        elif intent == 'manage_booking.flight.question - otras - yes':
            self.fb_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - otras - no':
            self.fb_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - yes':
            self.fb_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - no':
            self.fb_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='facebook',
                language=language
            )
            self.fb_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='facebook',
                department="Flight+Hotel"
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel':
            self.fb_bot.send_manage_booking_options(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='facebook',
                language=language
            )
            self.fb_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='facebook',
                department="Flight+Hotel"
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance' \
                       ' - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='facebook',
                language=language
            )
            self.fb_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance' \
                       ' - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='facebook',
                department="Flight+Hotel"
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.question':
            self.fb_bot.send_have_question(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_have_question(
                recipient_id=recipient_id,
                language=language,
                channel='facebook'
            )
        elif intent == 'manage_booking.flight_hotel.question - yes':
            self.fb_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.question - no':
            self.fb_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.cancel':
            self.fb_bot.send_cancel(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_cancel(
                recipient_id=recipient_id,
                language=language,
                channel='facebook'
            )
        elif intent == 'manage_booking.hotel.cancel - yes':
            self.fb_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.cancel - no':
            self.fb_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel':
            self.fb_bot.send_manage_booking_options(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='facebook',
                language=language
            )
            self.fb_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='facebook',
                department="Hotel"
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='facebook',
                language=language
            )
            self.fb_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='facebook'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='facebook',
                department="Hotel"
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.question':
            self.fb_bot.send_have_question(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_have_question(
                recipient_id=recipient_id,
                language=language,
                channel='facebook'
            )
        elif intent == 'manage_booking.hotel.question - yes':
            self.fb_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.question - no':
            self.fb_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking':
            self.fb_bot.send_manage_booking(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation.flight':
            self.fb_bot.send_new_reservation_flight(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation - viaje':
            self.fb_bot.send_new_reservation_viaje(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation.flight_hotel':
            self.fb_bot.send_new_reservation_flight_hotel(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation.hotel':
            self.fb_bot.send_new_reservation_hotel(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation':
            self.fb_bot.send_new_reservation(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'question':
            self.fb_bot.send_have_question(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_have_question(
                recipient_id=recipient_id,
                language=language,
                channel='facebook'
            )
        elif intent == 'question - yes':
            self.fb_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'question - no':
            self.fb_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'start_again':
            self.fb_bot.send_start_over(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'greeting':
            self.fb_bot.send_greeting(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'thanks':
            self.fb_bot.send_thanks_response(
                recipient_id=recipient_id,
                language=language
            )
        return intent

    def route_telegram_prediction(self, user_id, recipient_id,
                                  message, full_obj, user_last_lang,
                                  current_locale):
        intent, language = self.engine.predict(
            user_id=user_id,
            message=message,
            last_lang=user_last_lang,
            current_locale=current_locale
        )
        self.set_user_last_lang(
            user_id=user_id,
            new_lang=language
        )
        LOGGER.info(intent)
        if intent == 'Default Fallback Intent':
            self.telegram_bot.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='telegram',
                language=language,
                full_obj=full_obj
            )
            self.telegram_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.fb_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.cancel':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='telegram',
                department="Flight"
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight':
            self.telegram_bot.send_manage_booking_options(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='telegram',
                language=language,
                full_obj=full_obj
            )
            self.telegram_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.make_changes':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='telegram',
                department="Flight"
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='telegram',
                language=language,
                full_obj=full_obj
            )
            self.telegram_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.on_spot_assistance':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='telegram',
                department="Flight"
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question':
            self.telegram_bot.send_have_flight_question(
                recipient_id=recipient_id,
                language=language
            )
            if language == 'en':
                self.initiate_have_question(
                    recipient_id=recipient_id,
                    language=language,
                    channel='telegram'
                )
        elif intent == 'manage_booking.flight.question - equipaje':
            self.telegram_bot.send_have_question_equipaje(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - checkin':
            self.telegram_bot.send_have_question_checkin(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - otras':
            self.telegram_bot.send_have_question_otras(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_have_question(
                recipient_id=recipient_id,
                language=language,
                channel='telegram'
            )
        elif intent == 'manage_booking.flight.question - otras - no':
            self.telegram_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - otras - yes':
            self.telegram_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - yes':
            self.telegram_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight.question - no':
            self.telegram_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='telegram',
                language=language,
                full_obj=full_obj
            )
            self.telegram_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.cancel':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='telegram',
                department="Flight+Hotel"
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel':
            self.telegram_bot.send_manage_booking_options(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='telegram',
                language=language,
                full_obj=full_obj
            )
            self.telegram_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.make_changes':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='telegram',
                department="Flight+Hotel"
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance' \
                       ' - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='telegram',
                language=language,
                full_obj=full_obj
            )
            self.telegram_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance' \
                       ' - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.on_spot_assistance':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='telegram',
                department="Flight+Hotel"
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.question':
            self.telegram_bot.send_have_question(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_have_question(
                recipient_id=recipient_id,
                language=language,
                channel='telegram'
            )
        elif intent == 'manage_booking.flight_hotel.question - yes':
            self.telegram_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.flight_hotel.question - no':
            self.telegram_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.cancel':
            self.telegram_bot.send_cancel(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_cancel(
                recipient_id=recipient_id,
                language=language,
                channel='telegram'
            )
        elif intent == 'manage_booking.hotel.cancel - yes':
            self.telegram_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.cancel - no':
            self.telegram_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel':
            self.telegram_bot.send_manage_booking_options(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='telegram',
                language=language,
                full_obj=full_obj
            )
            self.telegram_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.make_changes':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='telegram',
                department="Hotel"
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance - no - no':
            self.initiate_send_report(
                recipient_id=recipient_id,
                channel='telegram',
                language=language,
                full_obj=full_obj
            )
            self.telegram_bot.send_sent_request(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance - no - yes':
            self.initiate_wait_second_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance - no':
            self.initiate_wait_confirmation_number_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_request_confirmation_number(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance - yes':
            self.initiate_wait_request_session(
                recipient_id=recipient_id,
                channel='telegram'
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.on_spot_assistance':
            self.initiate_wait_first_request_session(
                recipient_id=recipient_id,
                channel='telegram',
                department="Hotel"
            )
            self.telegram_bot.send_how_can_we_help(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.question':
            self.telegram_bot.send_have_question(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_have_question(
                recipient_id=recipient_id,
                language=language,
                channel='telegram'
            )
        elif intent == 'manage_booking.hotel.question - yes':
            self.telegram_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking.hotel.question - no':
            self.telegram_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'manage_booking':
            self.telegram_bot.send_manage_booking(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation.flight':
            self.telegram_bot.send_new_reservation_flight(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation - viaje':
            self.telegram_bot.send_new_reservation_viaje(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation.flight_hotel':
            self.telegram_bot.send_new_reservation_flight_hotel(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation.hotel':
            self.telegram_bot.send_new_reservation_hotel(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'new_reservation':
            self.telegram_bot.send_new_reservation(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'question':
            self.telegram_bot.send_have_question(
                recipient_id=recipient_id,
                language=language
            )
            self.initiate_have_question(
                recipient_id=recipient_id,
                language=language,
                channel='telegram'
            )
        elif intent == 'question - yes':
            self.telegram_bot.send_yes_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'question - no':
            self.telegram_bot.send_no_question_solved(
                recipient_id=recipient_id,
                language=language
            )
        elif intent == 'start_again':
            self.telegram_bot.send_start_over(
                recipient_id=recipient_id,
                language=language,
                full_obj=full_obj
            )
        elif intent == 'greeting':
            self.telegram_bot.send_greeting(
                recipient_id=recipient_id,
                language=language,
                full_obj=full_obj
            )
        elif intent == 'thanks':
            self.telegram_bot.send_thanks_response(
                recipient_id=recipient_id,
                language=language,
                full_obj=full_obj
            )
        return intent
