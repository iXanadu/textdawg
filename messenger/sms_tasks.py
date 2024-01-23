import os
from celery import shared_task
from twilio.rest import Client
from .sms_conversation_manager import SMSConversationManager
import logging
logger = logging.getLogger(__name__)

logger.info(f"Entering messenger.smstasks.process_sms_message")



@shared_task
def process_sms_message(to_phone, from_phone, user_input):
    logger.info(f"Process_sms_message({to_phone},{from_phone},{user_input}")

    c = SMSConversationManager(temperature=0.0, model_name="gpt-4-1106-preview")
    response = c.respond_to_input(from_phone, to_phone, user_input)
    logger.info(f"Conversation-response({response['output']}")

    # Send response back to user using Twilio API
    client = Client(os.environ['TWILIO_SID'],os.environ['TWILIO_AUTH_TOKEN'])
    message = client.messages.create(
        to=from_phone,
        from_ = to_phone,
        body=response['output']
    )

