import math
import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from extensions import (
    LOGGER
)


class Bot:
    def __init__(self, access_token, **kwargs):
        """
            @required:
                access_token
            @optional:
                api_version
                app_secret
        """

        self.access_token = access_token
        self.bot = telegram.Bot(token=access_token)

    def send_message(self, recipient_id, message, parse_mode="HTML"):
        message = u"" + message
        self.bot.sendMessage(
            chat_id=recipient_id,
            text=message.encode('utf-8').decode(),
            parse_mode=parse_mode
        )

    def send_keyboard_message(self, recipient_id, message, buttons):
        reply_keyboard = [InlineKeyboardButton(b, callback_data=b)
                          for b in buttons]
        keyboard = []
        for i in range(0, len(reply_keyboard), 2):
            keyboard.append(reply_keyboard[i:i + 2])
        message = u"" + message
        self.bot.sendMessage(
            chat_id=recipient_id,
            text=message.encode('utf-8').decode(),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    @staticmethod
    def get_user_info(full_obj):
        user = full_obj.chat
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "name": user.first_name + ' ' + user.last_name
        }

# ############################## Responses ###############################
    def send_default_error(self, recipient_id, language):
        if language == 'en':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="I'm sorry I can not solve this question,"
                        " but I can help you with any of this options.",
                buttons=[
                    'New reservation',
                    'Manage a booking',
                    'I have a question',
                    'Start again'
                ]
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="No puedo resolver esa consulta pero "
                        "te puedo ayudar con alguna de estas opciones",
                buttons=[
                    'Buscar ofertas',
                    'Tengo una consulta',
                    'Ayuda con mi reserva',
                    'Empezar de nuevo'
                ]
            )

    def send_greeting(self, recipient_id, language, full_obj):
        user_info = self.get_user_info(
            full_obj=full_obj
        )
        name = user_info.get('name')
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message="Hi {name}, I'm Iris, your digital travel agent."
                        " I'm here to save you hours of research time and "
                        "help you to manage your bookings!".format(
                            name=name
                        )
            )
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="What can I do for you?",
                buttons=[
                    'New reservation',
                    'Manage a booking',
                    'I have a question',
                    'Start again',
                ]
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message="¡Hola! Soy Iris, el asistente virtual de Destinia "
            )
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Cuéntame, ¿qué necesitas?",
                buttons=[
                    'Buscar ofertas',
                    'Tengo una consulta',
                    'Ayuda con mi reserva',
                    'Empezar de nuevo'
                ]
            )

    def send_thanks_response(self, recipient_id, language, full_obj):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message="Glad to help."
            )
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="What can I do for you?",
                buttons=[
                    'New reservation',
                    'Manage a booking',
                    'I have a question',
                    'Start again',
                ]
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message="Encantado de ayudar."
            )
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Cuéntame, ¿qué necesitas?",
                buttons=[
                    'Buscar ofertas',
                    'Tengo una consulta',
                    'Ayuda con mi reserva',
                    'Empezar de nuevo'
                ]
            )

    def send_start_over(self, recipient_id, language, full_obj):
        if language == 'en':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="What can I do for you?",
                buttons=[
                    'New reservation',
                    'Manage a booking',
                    'I have a question',
                    'Start again',
                ]
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Cuéntame, ¿qué necesitas?",
                buttons=[
                    'Buscar ofertas',
                    'Tengo una consulta',
                    'Ayuda con mi reserva',
                    'Empezar de nuevo'
                ]
            )

    def send_new_reservation(self, recipient_id, language):
        if language == 'en':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="To get started just tell me what you're looking for",
                buttons=[
                    'Hotel',
                    'Flight',
                    'Flight+Hotel'
                ]
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="¡Genial! Dime qué buscas, y encontraré"
                        " para ti nuestras mejores ofertas",
                buttons=[
                    'Quiero un hotel',
                    'Quiero un vuelo',
                    'Quiero un viaje',
                    'Quiero un vuelo+hotel'
                ]
            )

    def send_new_reservation_hotel(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message='Click <a href="https://destinia.com/hotels/es">'
                        'here</a> to find the best hotel deals'
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message='Encuentra tu hotel al mejor precio,'
                        '<a href="https://destinia.com/hotels/es">aqui</a>'
            )

    def send_new_reservation_flight(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message='Click <a href="https://vuelos.destinia.com/">here</a>'
                        ' to book your flight at the best price',
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message='<a href="https://vuelos.destinia.com/">Aqui</a>'
                        ' tienes nuestras mejores ofertas de vuelos'
            )

    def send_new_reservation_viaje(self, recipient_id, language):
        if language == 'en':
            self.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message='El viaje de tus sueños, a tan sólo un clic <a '
                        'href="https://destinia.com/viajes/">aqui</a>'
            )

    def send_new_reservation_flight_hotel(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message='click <a href="https://destinia.com/vuelo'
                        '_mas_hotel/">here</a> to find our best deals',
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message='Super ofertas de vuelo+hotel <a '
                        'href="https://destinia.com/vuelo_mas_hotel/">aqui</a>'
            )

    def send_manage_booking(self, recipient_id, language):
        if language == 'en':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message='To get started, I need to know '
                        'what kind of reservation you have',
                buttons=[
                    'Hotel',
                    'Flight',
                    'Flight+Hotel'
                ]
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Para poder ayudarte necesito saber"
                        " si tu reserva es de...",
                buttons=[
                    'Hotel',
                    'Vuelo',
                    'Viaje',
                    'Vuelo+hotel'
                ]
            )

    def send_manage_booking_options(self, recipient_id, language):
        if language == 'en':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Please choose one of these options",
                buttons=[
                    "On spot assistance",
                    "I have a question",
                    "Make changes",
                    "Cancellation",
                    "Start again"
                ]
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="¿Cómo te podemos ayudar?",
                buttons=[
                    "Incidencia urgente",
                    "Tengo una consulta",
                    "Modificacion",
                    "Cancelacion",
                    "Empezar de nuevo"
                ]
            )

    def send_how_can_we_help(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message="OK! tell me, how can we help?"
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message="Cuéntame qué necesitas"
            )

    def send_request_confirmation_number(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message="Ok. What's your confirmation number?"
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message="Ok. Dime tu número de reserva o tu email de contacto"
            )

    def send_anything_else(self, recipient_id, language):
        if language == 'en':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Anything else?",
                buttons=[
                    "Yes",
                    "No"
                ]
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="¿algo más que añadir?",
                buttons=[
                    "Si",
                    "No"
                ]
            )

    def send_ask_another_request(self, recipient_id, language):
        if language == 'en':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Do you have any other request?",
                buttons=[
                    "Yes",
                    "No"
                ]
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="¿tienes alguna otra petición?",
                buttons=[
                    "Si",
                    "No"
                ]
            )

    def send_have_flight_question(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message='Check our <a href="https://destinia.com/m/faqs">'
                        'Help Center</a>, you will find answers '
                        'to the most common questions of our clients  :)',
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Necesito saber si tu pregunta es sobre...",
                buttons=[
                    "facturación online",
                    "Equipaje",
                    "Otros"
                ]
            )

    def send_have_question(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message='Check our <a href="https://destinia.com/m/faqs">'
                        'Help Center</a>, you will find answers '
                        'to the most common questions of our clients  :)',
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message='Échale un ojo a nuestro <a href="https://de'
                        'stinia.com/m/faqs">Centro de ayuda</a>, Aqui están '
                        'las preguntas más frecuentes de nuestros clientes.',
            )

    def send_have_question_otras(self, recipient_id, language):
        if language == 'en':
            self.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message='Échale un ojo a nuestro <a href="https://de'
                        'stinia.com/m/faqs">Centro de ayuda</a>, Aqui están '
                        'las preguntas más frecuentes de nuestros clientes.',
            )

    def send_have_question_checkin(self, recipient_id, language):
        if language == 'en':
            self.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message="24-48h antes de la salida de tu vuelo te enviaremos "
                        "un email con un enlace para hacer el check in online "
                        "y toda la informacion que necesitas para hacerlo."
            )

    def send_have_question_equipaje(self, recipient_id, language):
        if language == 'en':
            self.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message="Durante el proceso de compra se indicara si el"
                        " billete incluye o no el equipaje. Si quieres incluir"
            )

    def send_cancel(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message='You can cancel your booking'
                        ' through your <a href="https://res.destinia.com/'
                        'my-account/login?">'
                        'account</a> in our website.',
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message='Puedes cancelar tu reserva desde el apartado '
                        '<a href="https://res.destinia.com/my-acc'
                        'ount/login?">Mi cuenta'
                        '</a> en nuestra web',
            )

    def send_ask_question_solved(self, recipient_id, language):
        if language == 'en':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="Have been your question solved?",
                buttons=[
                    "Yes",
                    "No"
                ]
            )
        elif language == 'es':
            self.send_keyboard_message(
                recipient_id=recipient_id,
                message="¿Has resuelto tu duda?",
                buttons=[
                    "Si",
                    "No"
                ]
            )

    def send_yes_question_solved(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message="Great! Just let me know if there's"
                        " something else that I can do for you :)"
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message="¡Genial! Si necesitas algo más sólo"
                        " tienes que avisarme :)"
            )

    def send_no_question_solved(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message='Click <a href="https://res.destinia.com/contact/reser'
                        'vations">here</a> to send your question to a booking '
                        'agent who will answer as soon as possible',
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message='Haz clic <a href="https://res.destinia.com/contact/r'
                        'eservations">aqui</a> para enviar tu consulta a un '
                        'companero que contestara a la mayor brevedad posible',
            )

    def send_sent_request(self, recipient_id, language):
        if language == 'en':
            self.send_message(
                recipient_id=recipient_id,
                message="I just sent your request to a booking agent"
                        " that will reply you as soon as possible."
            )
        elif language == 'es':
            self.send_message(
                recipient_id=recipient_id,
                message="¡Genial!Ya he enviado tu solicitud. Si necesitas "
                        "algo más sólo tienes que avisarme 🙂"
            )
