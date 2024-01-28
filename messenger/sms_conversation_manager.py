import logging
from dotenv import load_dotenv
from django.utils import timezone
from main.models import FUBMessageUser, FubMessageHistory, OpenAIPrompt
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from crm.fub_api_handler import FUBApiHandler
from .sms_base_assistant import SMSAIBaseAssistant
import os


logger = logging.getLogger(__name__)


class SMSConversationManager:
    def __init__(self, temperature, model_name):
        load_dotenv()
        self.model_temp = temperature
        self.model_name = model_name
        self.fub_handler = FUBApiHandler(os.getenv('FUB_API_URL'), os.getenv('FUB_API_KEY'),
                                         os.getenv('FUB_X_SYSTEM'), os.getenv('FUB_X_SYSTEM_KEY'))
        self.assistant = SMSAIBaseAssistant(self.model_temp,self.model_name)

    def get_or_add_message_user(self, phone_number, query=''):
        msg_user = FUBMessageUser.objects.filter(phone_number=phone_number).first()
        if msg_user:
            return msg_user
        else:
            response = self.fub_handler.get_contact_from_fub(0, phone_number)
            if response:
                firstName = ''
                lastName = ''
                fubId = response["fubId"]
                if response["firstName"] != "No name":
                    firstName = response["firstName"]
                if response["lastName"] != "":
                    lastName = response["lastName"]
                email = response.get('emails', [{}])[0].get('value', 'No email found')

                logger.info(response)
                msg_user = FUBMessageUser(phone_number=phone_number, firstname=firstName,
                                          fubId=fubId, lastname=lastName, email=email, message_count=1)
                msg_user.save()
                self.fub_handler.add_update_fub_contact(fubId, phone_number, query)
            else:
                fubId = self.fub_handler.add_update_fub_contact(0, phone_number, query)
                msg_user = FUBMessageUser(phone_number=phone_number, fubId=fubId, message_count=1)
                msg_user.save()

        return msg_user

    def add_message_to_history(self, message_user,  message_text, message_role):
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
        chat_history = ConversationBufferMemory(input_key='input',
                                                memory_key='chat_history',
                                                return_messages=True)

        for input_message, output_message in io_records:
            input_text = input_message.message if input_message else None
            output_text = output_message.message if output_message else None

            # Call your save_context function with each pair of input and output
            chat_history.save_context({"input": input_text}, {"output": output_text})

        return chat_history

    def respond_to_input(self, user_phone, system_phone, user_input):
        msg_user = self.get_or_add_message_user(user_phone, user_input)
        chat_history = self.process_chat_history(user_phone)
        self.assistant.setup_agent(chat_history, msg_user)
        if msg_user.message_count == 1:
            prompt = self.assistant.get_ai_instructions()
            self.add_message_to_history(msg_user, prompt,'System')
        else:
            self.fub_handler.log_fub_text_message(False,msg_user.fubId,system_phone,
                                                  msg_user.phone_number, user_input)

        response = self.assistant.respond_to_input(user_input)

        self.fub_handler.log_fub_text_message(True, msg_user.fubId,msg_user.phone_number, system_phone,
                      response['output'])
        self.add_message_to_history(msg_user, user_input, 'Human')
        self.increment_user_message_count(msg_user)
        self.add_message_to_history(msg_user, response['output'], 'AI')
        return response


