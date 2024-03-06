import logging
from dotenv import load_dotenv
from django.utils import timezone
from main.models import FUBMessageUser, FubMessageHistory
from langchain.memory import ChatMessageHistory
from FUBHandler.fub_api_handler import FUBApiHandler
from .sms_base_assistant import SMSAIBaseAssistant
import os

# from icecream import ic

logger = logging.getLogger(__name__)


class SMSConversationManager:
    def __init__(self, temperature, model_name):
        load_dotenv()
        self.model_temp = temperature
        self.model_name = model_name
        self.fub_handler = FUBApiHandler(os.getenv('FUB_API_URL'), os.getenv('FUB_API_KEY'),
                                         os.getenv('FUB_X_SYSTEM'), os.getenv('FUB_X_SYSTEM_KEY'))
        self.assistant = SMSAIBaseAssistant(self.model_temp, self.model_name)
        self.server_msgId = 0
        self.user_msgId = 0

    def get_or_add_message_user(self, phone_number, query=''):
        tags = ["textDawg Lead", query]
        stage = "Lead"
        source = "textDawg"
        system = "textDawg"
        event_type = "Inquiry"

        message = f"User texted {query}"
        phones = self.fub_handler.build_phone_packet(None, phone_number, "Mobile", "Valid", True)

        msg_user = FUBMessageUser.objects.filter(phone_number=phone_number).first()
        if msg_user:
            return msg_user
        else:
            response = self.fub_handler.get_contact_from_fub(0, phone_number)
            if response:
                first_name = ''
                last_name = ''
                fub_id = response["fubId"]
                if response["firstName"] != "No name":
                    first_name = response["firstName"]
                if response["lastName"] != "":
                    last_name = response["lastName"]
                email = response.get('emails', [{}])[0].get('value', 'No email found')

                logger.info(response)
                msg_user = FUBMessageUser(phone_number=phone_number, firstname=first_name,
                                          fubId=fub_id, lastname=last_name, email=email, message_count=1)
                msg_user.save()
                # self.fub_handler.add_update_fub_contact(fubId, type, phone_number, stage, tags,
                # source, system, message, description)
                person = self.fub_handler.build_person_packet(False, fub_id, "", "", stage, source, 0, 0, None, phones,
                                                              None, tags)
                self.fub_handler.add_update_fub_contact(person, event_type, message, source, system, None)
            else:
                # fubId = self.fub_handler.add_update_fub_contact(0, type, phone_number, stage, tags,
                # source, system, message, description)
                person = self.fub_handler.build_person_packet(False, 0, "", "", stage, source, 0, 0, None, phones, None,
                                                              tags)
                response = self.fub_handler.add_update_fub_contact(person, event_type, message, source, system, None)
                fub_id = response['id']
                msg_user = FUBMessageUser(phone_number=phone_number, fubId=fub_id, message_count=1)
                msg_user.save()

        return msg_user

    def add_message_to_history(self, message_user, message_text, message_role):
        # Create a new MessageHistory instance
        new_message = FubMessageHistory(
            timestamp=timezone.now(),
            fubId=message_user.fubId,
            phone_number=message_user.phone_number,
            role=message_role,
            message=message_text,
            status='Delivered',
            message_user=message_user
        )
        new_message.save()
        return new_message.id

    def increment_user_message_count(self, message_user):
        message_user.message_count += 1
        message_user.save()

    def create_complete_io_records(self, phone_number):
        message_user = FUBMessageUser.objects.get(phone_number=phone_number)
        messages = message_user.message_history.order_by('timestamp')

        records = []
        pending_human_input = None
        pending_ai_output = None

        for message in messages:
            if message.role == "Human":
                if pending_ai_output is not None:
                    records.append((None, pending_ai_output))
                    pending_ai_output = None

                if pending_human_input is not None:
                    records.append((pending_human_input, None))

                pending_human_input = message

            elif message.role == "AI":
                if pending_human_input is not None:
                    records.append((pending_human_input, message))
                    pending_human_input = None
                else:
                    pending_ai_output = message

        if pending_human_input is not None:
            records.append((pending_human_input, None))
        if pending_ai_output is not None:
            records.append((None, pending_ai_output))

        return records

    def process_chat_history(self, phone_number):
        io_records = self.create_complete_io_records(phone_number)

        chat_history = ChatMessageHistory()
        for input_message, output_message in io_records:
            chat_history.add_user_message(input_message.message) if input_message else None
            chat_history.add_ai_message(output_message.message) if output_message else None

        return chat_history

    # def process_chat_history(self, phone_number):
    #         io_records = self.create_complete_io_records(phone_number)
    #         chat_history = ConversationBufferMemory(input_key='input',
    #                                                 memory_key='chat_history',
    #                                                 return_messages=True)
    #
    #         for input_message, output_message in io_records:
    #             input_text = input_message.message if input_message else None
    #             output_text = output_message.message if output_message else None
    #
    #             # Call your save_context function with each pair of input and output
    #             chat_history.save_context({"input": input_text}, {"output": output_text})
    #
    #         return chat_history

    def respond_to_input(self, user_phone, system_phone, user_input):
        msg_user = self.get_or_add_message_user(user_phone, user_input)
        chat_history = self.process_chat_history(user_phone)

        self.assistant.setup_agent(chat_history, msg_user)
        sys_msg = self.assistant.sys_msg
        if msg_user.message_count == 1:
            self.add_message_to_history(msg_user, sys_msg, 'System')
        else:
            self.fub_handler.log_fub_text_message(False, msg_user.fubId, system_phone,
                                                  msg_user.phone_number, user_input)

        response = self.assistant.respond_to_input(user_input)

        self.fub_handler.log_fub_text_message(True, msg_user.fubId, msg_user.phone_number, system_phone,
                                              response['output'])
        self.user_msgId = self.add_message_to_history(msg_user, user_input, 'Human')
        self.increment_user_message_count(msg_user)
        self.server_msgId = self.add_message_to_history(msg_user, response['output'], 'AI')
        logger.info(f"Server Message ID = {self.server_msgId}")
        return response
