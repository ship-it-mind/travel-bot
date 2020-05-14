from enum import Enum

import requests
from extensions import (
    FB_PAGE_ACCESS_TOKEN,
    LOGGER
)

DEFAULT_API_VERSION = 2.6


class NotificationType(Enum):
    regular = "REGULAR"
    silent_push = "SILENT_PUSH"
    no_push = "NO_PUSH"


class Bot:
    def __init__(self, access_token, **kwargs):
        """
            @required:
                access_token
            @optional:
                api_version
                app_secret
        """

        self.api_version = kwargs.get('api_version') or DEFAULT_API_VERSION
        self.app_secret = kwargs.get('app_secret')
        self.graph_url = 'https://graph.facebook.com/v{0}'.format(
            self.api_version)
        self.access_token = access_token
        self._auth_args = None

    @property
    def auth_args(self):
        auth = {
            'access_token': FB_PAGE_ACCESS_TOKEN
        }
        return auth

    def send_recipient(self, recipient_id, payload,
                       notification_type=NotificationType.regular):
        payload['recipient'] = {
            'id': recipient_id
        }
        payload['notification_type'] = notification_type.value
        return self.send_raw(payload)

    def send_message(self, recipient_id, message,
                     notification_type=NotificationType.regular):
        self.send_action(
            recipient_id=recipient_id,
            action='mark_seen'
        )

        self.send_action(
            recipient_id=recipient_id,
            action='typing_on'
        )

        message_req = self.send_recipient(recipient_id, {
            'message': message
        }, notification_type)

        self.send_action(
            recipient_id=recipient_id,
            action='typing_off'
        )
        return message_req

    def send_attachment_url(self, recipient_id, attachment_type,
                            attachment_url,
                            notification_type=NotificationType.regular):
        """Send an attachment to the specified recipient using URL.
        Input:
            recipient_id: recipient id to send to
            attachment_type: type of attachment (image, video, audio, file)
            attachment_url: URL of attachment
        Output:
            Response from API as <dict>
        """
        return self.send_message(recipient_id, {
            'attachment': {
                'type': attachment_type,
                'payload': {
                    'url': attachment_url
                }
            }
        }, notification_type)

    def send_text_message(self, recipient_id, message,
                          notification_type=NotificationType.regular):
        """Send text messages to the specified recipient.
        https://developers.facebook.com/docs/messenger-platform/
        send-api-reference/text-message
        Input:
            recipient_id: recipient id to send to
            message: message to send
        Output:
            Response from API as <dict>
        """
        return self.send_message(recipient_id, {
            'text': message
        }, notification_type)

    def send_generic_message(self, recipient_id, elements,
                             notification_type=NotificationType.regular):
        """Send generic messages to the specified recipient.
        https://developers.facebook.com/docs/messenger-platform/
        send-api-reference/generic-template
        Input:
            recipient_id: recipient id to send to
            elements: generic message elements to send
        Output:
            Response from API as <dict>
        """
        return self.send_message(recipient_id, {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }, notification_type)

    def send_button_message(self, recipient_id, text, buttons,
                            notification_type=NotificationType.regular):
        """Send text messages to the specified recipient.
        https://developers.facebook.com/docs/messenger-platform/
        send-api-reference/button-template
        Input:
            recipient_id: recipient id to send to
            text: text of message to send
            buttons: buttons to send
        Output:
            Response from API as <dict>
        """
        return self.send_message(recipient_id, {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": text,
                    "buttons": buttons
                }
            }
        }, notification_type)

    def send_list_message(self, recipient_id, text, list_items,
                          notification_type=NotificationType.regular):

        self.send_text_message(
            recipient_id=recipient_id,
            message=text
        )

        return self.send_generic_message(recipient_id,
                                         list_items, notification_type)

    def send_action(self, recipient_id, action,
                    notification_type=NotificationType.regular):
        """Send typing indicators or send read receipts
        to the specified recipient.
        https://developers.facebook.com/docs/
        messenger-platform/send-api-reference/sender-actions
        Input:
            recipient_id: recipient id to send to
            action: action type (mark_seen, typing_on, typing_off)
        Output:
            Response from API as <dict>
        """
        return self.send_recipient(recipient_id, {
            'sender_action': action
        }, notification_type)

    def send_image_url(self, recipient_id, image_url,
                       notification_type=NotificationType.regular):
        """Send an image to specified recipient using URL.
        Image must be PNG or JPEG or GIF (more might be supported).
        https://developers.facebook.com/docs/messenger-platform/
        send-api-reference/image-attachment
        Input:
            recipient_id: recipient id to send to
            image_url: url of image to be sent
        Output:
            Response from API as <dict>
        """
        return self.send_attachment_url(recipient_id,
                                        "image", image_url, notification_type)

    def send_audio_url(self, recipient_id, audio_url,
                       notification_type=NotificationType.regular):
        """Send audio to specified recipient using URL.
        Audio must be MP3 or WAV
        https://developers.facebook.com/docs/messenger-platform/
        send-api-reference/audio-attachment
        Input:
            recipient_id: recipient id to send to
            audio_url: url of audio to be sent
        Output:
            Response from API as <dict>
        """
        return self.send_attachment_url(recipient_id,
                                        "audio", audio_url, notification_type)

    def send_video_url(self, recipient_id, video_url,
                       notification_type=NotificationType.regular):
        """Send video to specified recipient using URL.
        Video should be MP4 or MOV, but supports more
        (https://www.facebook.com/help/218673814818907).
        https://developers.facebook.com/docs/messenger-p
        latform/send-api-reference/video-attachment
        Input:
            recipient_id: recipient id to send to
            video_url: url of video to be sent
        Output:
            Response from API as <dict>
        """
        return self.send_attachment_url(recipient_id,
                                        "video", video_url, notification_type)

    def send_file_url(self, recipient_id, file_url,
                      notification_type=NotificationType.regular):
        """Send file to the specified recipient.
        https://developers.facebook.com/docs/messenger-
        platform/send-api-reference/file-attachment
        Input:
            recipient_id: recipient id to send to
            file_url: url of file to be sent
        Output:
            Response from API as <dict>
        """
        return self.send_attachment_url(recipient_id,
                                        "file", file_url, notification_type)

    def get_user_info(self, recipient_id, fields=None):
        """Getting information about the user
        https://developers.facebook.com/docs/messenger-platform/user-profile
        Input:
          recipient_id: recipient id to send to
        Output:
          Response from API as <dict>
        """
        params = {}
        if fields is not None and isinstance(fields, (list, tuple)):
            params['fields'] = ",".join(fields)

        params.update(self.auth_args)

        request_endpoint = '{0}/{1}'.format(self.graph_url, recipient_id)
        response = requests.get(request_endpoint, params=params)
        if response.status_code == 200:
            return response.json()

        return None

    def send_raw(self, payload):
        request_endpoint = '{0}/me/messages'.format(self.graph_url)
        response = requests.post(
            request_endpoint,
            params=self.auth_args,
            json=payload
        )
        result = response.json()
        LOGGER.error(result)
        return result

    def _send_payload(self, payload):
        """ Deprecated, use send_raw instead """
        return self.send_raw(payload)

    def set_get_started(self, gs_obj):
        """Set a get started button shown on welcome screen
        for first time users
        https://developers.facebook.com/docs/messenger-platform/
        reference/messenger-profile-api/get-started-button
        Input:
          gs_obj: Your formatted get_started object as
          described by the API docs
        Output:
          Response from API as <dict>
        """
        request_endpoint = '{0}/me/messenger_profile'.format(self.graph_url)
        response = requests.post(
            request_endpoint,
            params=self.auth_args,
            json=gs_obj
        )
        result = response.json()
        return result

    def set_persistent_menu(self, pm_obj):
        """Set a persistent_menu that stays same for every user.
        Before you can use this, make sure to have set a get
         started button.
        https://developers.facebook.com/docs/messenger-platform/
        reference/messenger-profile-api/persistent-menu
        Input:
          pm_obj: Your formatted persistent menu object as
          described by the API docs
        Output:
          Response from API as <dict>
        """
        request_endpoint = '{0}/me/messenger_profile'.format(self.graph_url)
        response = requests.post(
            request_endpoint,
            params=self.auth_args,
            json=pm_obj
        )
        result = response.json()
        return result

    def remove_get_started(self):
        """delete get started button.
        https://developers.facebook.com/docs/messenger-platform/
        reference/messenger-profile-api/#delete
        Output:
        Response from API as <dict>
        """
        delete_obj = {"fields": ["get_started"]}
        request_endpoint = '{0}/me/messenger_profile'.format(self.graph_url)
        response = requests.delete(
            request_endpoint,
            params=self.auth_args,
            json=delete_obj
        )
        result = response.json()
        return result

    def remove_persistent_menu(self):
        """delete persistent menu.
        https://developers.facebook.com/docs/messenger-platform/
        reference/messenger-profile-api/#delete
        Output:
        Response from API as <dict>
        """
        delete_obj = {"fields": ["persistent_menu"]}
        request_endpoint = '{0}/me/messenger_profile'.format(self.graph_url)
        response = requests.delete(
            request_endpoint,
            params=self.auth_args,
            json=delete_obj
        )
        result = response.json()
        return result

    def send_quick_replies(self, recipient_id, message, quick_replies,
                           notification_type=NotificationType.regular):
        """Send a quick reply to the specified recipient wi
        th specific type of quick reply.
        https://developers.facebook.com/docs/messenger-p
        latform/reference/send-api/quick-replies/
        Input:
            recipient_id: recipient id to send to
            text: Text to ask for something
            type: content_type. eg: text, location,
             user_phone_number, user_email
            title: Title of quick reply
            payload: Postback payload
            img_url: Icon URL for quick Reply suggestion
        Output:
            Response from API as <dict>
        """
        return self.send_message(recipient_id, {
            "text": message,
            "quick_replies": quick_replies
        }, notification_type)

# ############################## Responses ###############################

    def send_default_error(self, recipient_id, language):
        if language == 'en':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="I'm sorry I can not solve this question,"
                        " but I can help you with any of this options.",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'New reservation',
                        "payload": 'new_reservation'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Manage a booking',
                        "payload": 'manage_booking'
                    },
                    {
                        "content_type": 'text',
                        "title": 'I have a question',
                        "payload": 'question'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Start again',
                        "payload": 'start again'
                    },
                ]
            )
        elif language == 'es':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="No puedo resolver esa consulta pero "
                        "te puedo ayudar con alguna de estas opciones",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'Buscar ofertas',
                        "payload": 'buscar_ofertas'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Tengo una consulta',
                        "payload": 'tengo_consulta'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Ayuda con mi reserva',
                        "payload": 'ayuda_reserva'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Empezar de nuevo',
                        "payload": 'empezar_nuevo'
                    },
                ]
            )

    def send_greeting(self, recipient_id, language):
        user_info = self.get_user_info(
            recipient_id=recipient_id,
            fields=['name']
        )
        name = user_info.get('name')
        if language == 'en':
            self.send_text_message(
                recipient_id=recipient_id,
                message="Hi {name}, I’m Iris, your digital travel agent 🤖."
                        " I'm here to save you hours of research time and "
                        "help you to manage your bookings!".format(
                            name=name
                        )
            )
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="What can I do for you?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'New reservation',
                        "payload": 'new_reservation'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Manage a booking',
                        "payload": 'manage_booking'
                    },
                    {
                        "content_type": 'text',
                        "title": 'I have a question',
                        "payload": 'question'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Start again',
                        "payload": 'start again'
                    },
                ]
            )
        elif language == 'es':
            self.send_text_message(
                recipient_id=recipient_id,
                message="¡Hola! Soy Iris, el asistente virtual de Destinia "
            )
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="Cuéntame, ¿qué necesitas?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'Buscar ofertas',
                        "payload": 'buscar_ofertas'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Tengo una consulta',
                        "payload": 'tengo_consulta'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Ayuda con mi reserva',
                        "payload": 'ayuda_reserva'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Empezar de nuevo',
                        "payload": 'empezar_nuevo'
                    },
                ]
            )

    def send_thanks_response(self, recipient_id, language):
        if language == 'en':
            self.send_text_message(
                recipient_id=recipient_id,
                message="Glad to help."
            )
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="What can I do for you?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'New reservation',
                        "payload": 'new_reservation'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Manage a booking',
                        "payload": 'manage_booking'
                    },
                    {
                        "content_type": 'text',
                        "title": 'I have a question',
                        "payload": 'question'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Start again',
                        "payload": 'start again'
                    },
                ]
            )
        elif language == 'es':
            self.send_text_message(
                recipient_id=recipient_id,
                message="Encantado de ayudar."
            )
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="Cuéntame, ¿qué necesitas?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'Buscar ofertas',
                        "payload": 'buscar_ofertas'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Tengo una consulta',
                        "payload": 'tengo_consulta'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Ayuda con mi reserva',
                        "payload": 'ayuda_reserva'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Empezar de nuevo',
                        "payload": 'empezar_nuevo'
                    },
                ]
            )

    def send_start_over(self, recipient_id, language):
        if language == 'en':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="What can I do for you?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'New reservation',
                        "payload": 'new_reservation'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Manage a booking',
                        "payload": 'manage_booking'
                    },
                    {
                        "content_type": 'text',
                        "title": 'I have a question',
                        "payload": 'question'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Start again',
                        "payload": 'start again'
                    },
                ]
            )
        elif language == 'es':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="Cuéntame, ¿qué necesitas?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'Buscar ofertas',
                        "payload": 'buscar_ofertas'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Tengo una consulta',
                        "payload": 'tengo_consulta'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Ayuda con mi reserva',
                        "payload": 'ayuda_reserva'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Empezar de nuevo',
                        "payload": 'empezar_nuevo'
                    },
                ]
            )

    def send_new_reservation(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='To get started just tell me what you’re looking for',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/hotels/es",
                        "title": "Hotel"
                    },
                    {
                        "type": "web_url",
                        "url": "https://vuelos.destinia.com/",
                        "title": "Flight"
                    },
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/vuelo_mas_hotel/",
                        "title": "Flight+Hotel"
                    }
                ]
            )
        elif language == 'es':
            self.send_list_message(
                recipient_id=recipient_id,
                text="¡Genial! Dime qué buscas, y "
                     "encontraré para ti nuestras mejores ofertas",
                list_items=[
                    {
                        "title": "Quiero un hotel",
                        "subtitle": "Encuentra tu hotel al mejor precio, aquí",
                        "default_action": {
                            "type": "web_url",
                            "url": "https://destinia.com/hotels/es",
                            "messenger_extensions": False,
                            "webview_height_ratio": "tall"
                        }
                    },
                    {
                        "title": "Quiero un vuelo",
                        "subtitle": "Aquí tienes nuestras mejores"
                                    " ofertas de vuelos",
                        "default_action": {
                            "type": "web_url",
                            "url": "https://vuelos.destinia.com/",
                            "messenger_extensions": False,
                            "webview_height_ratio": "tall"
                        }
                    },
                    {
                        "title": "Quiero un viaje",
                        "subtitle": "El viaje de tus sueños"
                                    ", a tan sólo un clic",
                        "default_action": {
                            "type": "web_url",
                            "url": "https://destinia.com/viajes/",
                            "messenger_extensions": False,
                            "webview_height_ratio": "tall"
                        }
                    },
                    {
                        "title": "Quiero un vuelo + hotel",
                        "subtitle": "Súper ofertas de vuelo+hotel aquí",
                        "default_action": {
                            "type": "web_url",
                            "url": "https://destinia.com/vuelo_mas_hotel/",
                            "messenger_extensions": False,
                            "webview_height_ratio": "tall"
                        }
                    }
                ]
            )

    def send_new_reservation_hotel(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Click here to find the best hotel deals',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/hotels/es",
                        "title": "Hotel"
                    }
                ]
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Encuentra tu hotel al mejor precio, aquí',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/hotels/es",
                        "title": "Quiero un hotel"
                    }
                ]
            )

    def send_new_reservation_viaje(self, recipient_id, language):
        if language == 'en':
            self.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text='El viaje de tus sueños, a tan sólo un clic',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/viajes/",
                        "title": "Quiero un viaje"
                    }
                ]
            )

    def send_new_reservation_flight(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Click here to book your flight at the best price',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://vuelos.destinia.com/",
                        "title": "Flight"
                    }
                ]
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Aquí tienes nuestras mejores ofertas de vuelos',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://vuelos.destinia.com/",
                        "title": "Quiero un vuelo"
                    }
                ]
            )

    def send_new_reservation_flight_hotel(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Click here to find our best deals',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/vuelo_mas_hotel/",
                        "title": "Flight+Hotel"
                    }
                ]
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Súper ofertas de vuelo+hotel aquí',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/vuelo_mas_hotel/",
                        "title": "Quiero un vuelo + hotel"
                    }
                ]
            )

    def send_manage_booking(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='To get started, I need to know '
                     'what kind of reservation you have',
                buttons=[
                    {
                        "type": "postback",
                        "payload": "manage_booking_hotel",
                        "title": "Hotel"
                    },
                    {
                        "type": "postback",
                        "payload": "manage_booking_flight",
                        "title": "Flight"
                    },
                    {
                        "type": "postback",
                        "payload": "manage_booking_flight_hotel",
                        "title": "Flight+Hotel"
                    }
                ]
            )
        elif language == 'es':
            self.send_list_message(
                recipient_id=recipient_id,
                text="Para poder ayudarte necesito saber"
                     " si tu reserva es de...",
                list_items=[
                    {
                        "title": "Hotel",
                        "buttons": [{
                            "type": "postback",
                            "payload": "manage_booking_hotel",
                            "title": "Hotel"
                        }]
                    },
                    {
                        "title": "Vuelo",
                        "buttons": [{
                            "type": "postback",
                            "payload": "manage_booking_flight",
                            "title": "Vuelo"
                        }]
                    },
                    {
                        "title": "Viaje",
                        "buttons": [{
                            "type": "postback",
                            "payload": "manage_booking_flight_hotel",
                            "title": "Viaje"
                        }]
                    },
                    {
                        "title": "Vuelo + Hotel",
                        "buttons": [{
                            "type": "postback",
                            "payload": "manage_booking_flight_hotel",
                            "title": "Vuelo + Hotel"
                        }]
                    }
                ]
            )

    def send_manage_booking_options(self, recipient_id, language):
        if language == 'en':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="Please choose one of these options",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'On spot assistance',
                        "payload": 'assistance'
                    },
                    {
                        "content_type": 'text',
                        "title": 'I have a question',
                        "payload": 'I have a question'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Make changes',
                        "payload": 'Make changes'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Cancellation',
                        "payload": 'Cancellation'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Start again',
                        "payload": 'Start again'
                    }
                ]
            )
        elif language == 'es':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="¿Cómo te podemos ayudar?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'Incidencia urgente',
                        "payload": 'assistance'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Tengo una consulta',
                        "payload": 'I have a question'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Modificación',
                        "payload": 'Make changes'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Cancelación',
                        "payload": 'Cancellation'
                    },
                    {
                        "content_type": 'text',
                        "title": 'Empezar de nuevo',
                        "payload": 'Empezar de nuevo'
                    }
                ]
            )

    def send_how_can_we_help(self, recipient_id, language):
        if language == 'en':
            self.send_text_message(
                recipient_id=recipient_id,
                message="OK! tell me, how can we help?"
            )
        elif language == 'es':
            self.send_text_message(
                recipient_id=recipient_id,
                message="Cuéntame qué necesitas"
            )

    def send_request_confirmation_number(self, recipient_id, language):
        if language == 'en':
            self.send_text_message(
                recipient_id=recipient_id,
                message="Ok. What’s your confirmation number?"
            )
        elif language == 'es':
            self.send_text_message(
                recipient_id=recipient_id,
                message="Ok. Dime tu número de reserva"
            )

    def send_anything_else(self, recipient_id, language):
        if language == 'en':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="Anything else?",
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
        elif language == 'es':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="¿algo más que añadir?",
                quick_replies=[
                    {
                        "content_type": 'text',
                        "title": 'Si',
                        "payload": 'yes'
                    },
                    {
                        "content_type": 'text',
                        "title": 'no',
                        "payload": 'no'
                    }
                ]
            )

    def send_ask_another_request(self, recipient_id, language):
        if language == 'en':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="Do you have any other request?",
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
        elif language == 'es':
            self.send_quick_replies(
                recipient_id=recipient_id,
                message="¿tienes alguna otra petición?",
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

    def send_have_question(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Check our Help Center, you will find answers '
                     'to the most common questions of our clients  :)',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/m/faqs",
                        "title": "Help Center"
                    }
                ]
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text="Échale un ojo a nuestro Centro de ayuda,"
                     " Aquí están las preguntas más frecuentes de "
                     "nuestros clientes.",
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/m/faqs",
                        "title": "Centro de ayuda"
                    }
                ]
            )

    def send_have_flight_question(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Check our Help Center, you will find answers '
                     'to the most common questions of our clients  :)',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/m/faqs",
                        "title": "Help Center"
                    }
                ]
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text="Necesito saber si tu pregunta es sobre...",
                buttons=[
                    {
                        "type": "postback",
                        "title": "facturación online",
                        "payload": "facturación online"
                    },
                    {
                        "type": "postback",
                        "title": "Equipaje",
                        "payload": "Equipaje"
                    },
                    {
                        "type": "postback",
                        "title": "Otros",
                        "payload": "Otros"
                    },
                ]
            )

    def send_have_question_equipaje(self, recipient_id, language):
        if language == 'en':
            self.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif language == 'es':
            self.send_text_message(
                recipient_id=recipient_id,
                message="Durante el proceso de compra se indicará si el"
                        " billete incluye o no el equipaje. Si quieres incluir"
            )

    def send_have_question_checkin(self, recipient_id, language):
        if language == 'en':
            self.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif language == 'es':
            self.send_text_message(
                recipient_id=recipient_id,
                message="24-48h antes de la salida de tu vuelo te enviaremos "
                        "un email con un enlace para hacer el check in online "
                        "y toda la información que necesitas para hacerlo."
            )

    def send_have_question_otras(self, recipient_id, language):
        if language == 'en':
            self.send_default_error(
                recipient_id=recipient_id,
                language=language
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text="Échale un ojo a nuestro Centro de ayuda,"
                     " Aquí están las preguntas más frecuentes de "
                     "nuestros clientes.",
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://destinia.com/m/faqs",
                        "title": "Centro de ayuda"
                    }
                ]
            )

    def send_cancel(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='You can cancel your booking'
                     ' through your account in our website.',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://rebrand.ly/d42457",
                        "title": "My Account"
                    }
                ]
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Puedes cancelar tu reserva desde el apartado '
                     'Mi cuenta'
                     ' en nuestra web',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://rebrand.ly/d42457",
                        "title": "Mi cuenta"
                    }
                ]
            )

    def send_yes_question_solved(self, recipient_id, language):
        if language == 'en':
            self.send_text_message(
                recipient_id=recipient_id,
                message="Great! Just let me know if there's"
                        " something else that I can do for you :)"
            )
        elif language == 'es':
            self.send_text_message(
                recipient_id=recipient_id,
                message="¡Genial! Si necesitas algo"
                        " más sólo tienes que avisarme :)"
            )

    def send_no_question_solved(self, recipient_id, language):
        if language == 'en':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Click here to send your question to a booking '
                     'agent who will answer as soon as possible',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://res.destinia.com/contact/reservations",
                        "title": "Contact Us"
                    }
                ]
            )
        elif language == 'es':
            self.send_button_message(
                recipient_id=recipient_id,
                text='Haz clic aquí para enviar tu consulta a un'
                     ' compañero que contestará a la mayor brevedad posible',
                buttons=[
                    {
                        "type": "web_url",
                        "url": "https://res.destinia.com/contact/reservations",
                        "title": "Contactar"
                    }
                ]
            )

    def send_sent_request(self, recipient_id, language):
        if language == 'en':
            self.send_text_message(
                recipient_id=recipient_id,
                message="I just sent your request to a booking agent"
                        " that will reply you as soon as possible."
            )
        elif language == 'es':
            self.send_text_message(
                recipient_id=recipient_id,
                message="¡Genial!Ya he enviado tu solicitud. "
                        "Si necesitas algo más sólo tienes que avisarme :)"
            )
