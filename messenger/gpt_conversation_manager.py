from dotenv import load_dotenv
from django.utils import timezone
from main.models import FUBMessageUser, FubMessageHistory
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from .gpt_base_assistant import GPTAIBaseAssistant
import os

class GPTConversationManager:
    def __init__(self, temperature, model_name):
        load_dotenv()
        self.model_temp = temperature
        self.model_name = model_name
        self.assistant = GPTAIBaseAssistant(self.model_temp, self.model_name)

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
    # Call the function to process records
    def respond_to_input(self, user_input):
        # chat_history = self.process_chat_history(phone_number)

        # self.add_message_to_history(msg_user, prompt,'System')

        chat_history = ConversationBufferMemory(input_key='input',
                                                memory_key='chat_history',
                                                return_messages=True)
        self.assistant.setup_agent(chat_history)
        response = self.assistant.respond_to_input(user_input)

        # self.add_message_to_history(msg_user, user_input, 'Human')
        # self.add_message_to_history(msg_user, response['output'], 'AI')
        return response


