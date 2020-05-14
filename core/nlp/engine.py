import os
from dotenv import load_dotenv
import dialogflow_v2 as dialogflow
from guess_language import guess_language
from yandex_translate import YandexTranslate

from extensions import LOGGER

basedir = os.path.abspath(os.path.dirname(__file__))

dot_env_path = os.path.join(os.path.dirname(__file__),
                            os.path.join(os.getcwd(), '.env'))
load_dotenv(dot_env_path)

DIALOGFLOW_PROJECT_ID = os.getenv('DIALOGFLOW_PROJECT_ID')
PRETRAINED_MODEL_PATH = os.getenv('PRETRAINED_MODEL_PATH')


class NLPEngine:
    def __init__(self):
        self.session_client = dialogflow.SessionsClient()
        self.session_context = dialogflow.ContextsClient()
        self.neutral_words = [
            "bot",
            "chatbot",
            "iris",
            "chat bot",
            "hotel",
            "no",
        ]
        self.spanish_words = [
            "oy",
            "oye",
            "ey",
            "si"
        ]
        self.translate = YandexTranslate('trnsl.1.1.20200215T104617Z.e985952a7'
                                         'c20d3fc.45cea67a739d4bbe0d98177bb452'
                                         '7b84b0857455')

    def detect_language(self, text, last_lang='es', current_locale='es'):
        locale = self.get_current_locale(current_locale)
        if locale is None and last_lang is not None:
            locale = last_lang
        elif locale is None and last_lang is None:
            locale = "es"
        text = text.lower().strip()

        if len(text.split()) == 1:
            if text in self.neutral_words and last_lang is not None:
                return last_lang
            elif text in self.neutral_words and last_lang is None:
                return locale
            elif text in self.spanish_words:
                return "es"
            else:
                try:
                    language = self.translate.detect(text)
                    if language in ['en', 'es']:
                        return language
                    elif last_lang is not None:
                        return last_lang
                    else:
                        return 'es'
                except Exception:
                    return last_lang
        try:
            language = self.translate.detect(text)
            if language in ['en', 'es']:
                return language
            elif last_lang is not None:
                return last_lang
            else:
                return 'es'
        except Exception:
            return last_lang

    @staticmethod
    def get_current_locale(locale):
        if locale.startswith("en"):
            return "en"
        elif locale.startswith("es"):
            return "es"
        else:
            return None

    def predict(self, user_id, message, last_lang='es', current_locale='es'):
        language = self.detect_language(message, last_lang, current_locale)
        intent = self.detect_intent_texts(
            user_id=user_id,
            text=message,
            language_code= language
        )
        return intent

    def detect_intent_texts(self, user_id, text, language_code):
        """Returns the result of detect intent with texts as inputs.
    
        Using the same `user_id` between requests allows continuation
        of the conversation."""
        LOGGER.info(user_id)
        LOGGER.info(language_code)
        LOGGER.info(text)
        session = self.session_client.session_path(DIALOGFLOW_PROJECT_ID, user_id)
        context = self.session_context.session_path(DIALOGFLOW_PROJECT_ID, user_id)
        text_input = dialogflow.types.TextInput(
            text=text, language_code=language_code)
    
        query_input = dialogflow.types.QueryInput(text=text_input)
    
        response = self.session_client.detect_intent(
            session=session, query_input=query_input)
        intent = response.query_result.intent.display_name
        if intent.endswith("- no - no") or intent.endswith(".question - yes")\
                or intent.endswith(".question - no") or intent.endswith(
                ".hotel.cancel - yes") or\
                intent.endswith(".hotel.cancel - no"):
            LOGGER.info("Context Clear")
            self.session_context.delete_all_contexts(context)
    
        return intent, language_code
