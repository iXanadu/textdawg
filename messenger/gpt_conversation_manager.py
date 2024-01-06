from dotenv import load_dotenv
from django.utils import timezone
from main.models import FUBMessageUser, FubMessageHistory
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from .gpt_base_assistant import GPTAIBaseAssistant
from main.app_logger import setup_logger
from main.models import ChatTopic, ChatMessage
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required

import logging


class GPTConversationManager:
    def __init__(self, temperature, user, topic_text, topic_id, model_name):
        load_dotenv()
        self.model_temp = temperature
        self.model_name = model_name
        self.user = user
        self.assistant = GPTAIBaseAssistant(self.model_temp, self.model_name)
        self.logger = setup_logger('chat_server')
        self.topic_text = topic_text
        self.topic_id = topic_id
        print(f"messenger: {topic_id}")
        if self.topic_id:
            self.topic = self.get_topic_by_id(user, self.topic_id)
        else:
            self.topic = self.get_topic_by_text(user, topic_text)


    def get_topic_by_text(self, user, topic_text):
            try:
                topic = ChatTopic.objects.get(user=user, topic_text=topic_text)
                return topic
            except ChatTopic.DoesNotExist:
                return None

    def get_topic_by_id(self, user, topic_id):
        try:
            topic = ChatTopic.objects.get(user=user, id=topic_id)
            return topic
        except ChatTopic.DoesNotExist:
            return None

    def add_topic(self, user, topic_text):
        try:
            topic, created = ChatTopic.objects.get_or_create(user=user, topic_text=topic_text)
            return topic
        except Exception as e:
            self.logger.error(f"Error adding topic: {e}")
            return None

    def update_topic(self, topic_id, new_topic_text):
        try:
            topic = ChatTopic.objects.get(id=topic_id)
            topic.topic_text = new_topic_text
            topic.save()
            return topic
        except ObjectDoesNotExist:
            self.logger.error(f"Topic with id {topic_id} not found for update.")
            return None
        except Exception as e:
            self.logger.error(f"Error updating topic: {e}")
            return None

    def delete_topic(self, topic_id):
        try:
            ChatTopic.objects.filter(id=topic_id).delete()
        except Exception as e:
            self.logger.error(f"Error deleting topic with id {topic_id}: {e}")

    def add_message(self, topic_id, message_text, role):
        try:
            topic = ChatTopic.objects.get(id=topic_id)
            message = ChatMessage.objects.create(topic=topic, message_text=message_text, role=role)
            return message
        except ObjectDoesNotExist:
            self.logger.error(f"Topic with id {topic_id} not found for message.")
            return None
        except Exception as e:
            self.logger.error(f"Error adding message: {e}")
            return None

    def create_complete_io_records(self,topic):
        messages = ChatMessage.objects.filter(topic=topic).order_by('timestamp')

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

    def process_chat_history(self, topic):
        io_records = self.create_complete_io_records(topic)
        chat_history = ConversationBufferMemory(input_key='input',
                                                memory_key='chat_history',
                                                return_messages=True)

        for input_message, output_message in io_records:
            input_text = input_message.message_text if input_message else None
            output_text = output_message.message_text if output_message else None

            # Call your save_context function with each pair of input and output
            chat_history.save_context({"input": input_text}, {"output": output_text})

        return chat_history
    # Call the function to process records
    def respond_to_input(self, user_input):
        if not self.topic:
            if self.topic_text:
                self.topic = self.add_topic(self.user, self.topic_text)
            else:
                # Handle error: Neither topic_id nor topic_text provided
                return {"error": "Topic information not provided"}

        chat_history = self.process_chat_history(self.topic)
        print(chat_history)
        self.assistant.setup_agent(chat_history)
        self.add_message(self.topic.id, user_input, "Human")
        response = self.assistant.respond_to_input(user_input)
        self.add_message(self.topic.id, response['output'], "AI")

        # self.add_message_to_history(msg_user, user_input, 'Human')
        # self.add_message_to_history(msg_user, response['output'], 'AI')
        return response


