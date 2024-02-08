import logging
import json
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST, require_GET
from main.models import ChatTopic, ChatMessage,SMSMarkedMessage,FUBhookEvent,FubMessageHistory
from messenger.gpt_conversation_manager import GPTConversationManager
from messenger.sms_conversation_manager import SMSConversationManager
from messenger.sms_tasks import process_sms_message
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
import os
import hashlib
import base64
import hmac


logger = logging.getLogger(__name__)

@require_POST
def create_chat_topic(request):
    topic_text = request.POST.get('topic')
    topic, created = ChatTopic.objects.get_or_create(user=request.user, topic_text=topic_text)
    return JsonResponse({'topic_id': topic.id, 'topic_text': topic.topic_text, 'created': created})

@login_required
@require_GET
def list_chat_topics(request):
    topics = ChatTopic.objects.filter(user=request.user).values('id', 'topic_text')
    response = JsonResponse(list(topics), safe=False)
    return response

@login_required
@require_GET
def get_chat_messages(request, topic_id):
    messages = ChatMessage.objects.filter(topic_id=topic_id).order_by('timestamp').values('message_text', 'role','timestamp')
    response = JsonResponse(list(messages), safe=False)
    return response

@login_required
@require_GET
def get_sms_messages(request, phone_number):
    digits = ''.join(filter(str.isdigit, phone_number))
    if len(digits) == 10:
        cleaned_phone_number = f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    elif len(digits) == 11:
        cleaned_phone_number = f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
    else:
        return HttpResponse(f"from-Phone must be 10 (or 11) digits ({digits})", status=405)

    messages = FubMessageHistory.objects.filter(phone_number=cleaned_phone_number).order_by('timestamp').values('message', 'role','timestamp')
    response = JsonResponse(list(messages), safe=False)
    return response

@csrf_exempt  # Disable CSRF protection for this view
def chat_receiver(request):
    if request.method == 'POST':
        user = request.user
        if not user:
            return HttpResponse('Method not allowed (login required)', status=405)

        print(request.POST)
        user_input = request.POST.get('user_input')
        new_topic = request.POST.get('new_topic', '').strip()
        topic_id = request.POST.get('topic_id')

        # Convert topic_id to integer if it's not None
        topic_id = int(topic_id) if topic_id else None

        # Instantiate the GPTConversationManager with both topic_id and topic_text
        c = GPTConversationManager(temperature=0.0, user=user, topic_text=new_topic, topic_id=topic_id,
                                   model_name="gpt-4-1106-preview")
        response = c.respond_to_input(user_input)

        return HttpResponse(response['output'], status=200)
    else:
        return HttpResponse('Method not allowed(invalid)', status=405)


@csrf_exempt  # Disable CSRF protection for this view
def sms_receiver(request):
    if request.method == 'POST':

        # Get the full request URL
        url = 'http://textdawg.com/webhook/sms_receiver/'

        # Get the POST data and headers
        post_vars = request.POST
        twilio_signature = request.headers.get('X-Twilio-Signature')

        # Create an instance of the RequestValidator
        validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))

        # Validate the request
        if validator.validate(url, post_vars, twilio_signature):
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')

            from_phone = request.POST.get('From')
            to_phone = request.POST.get('To')
            user_input = request.POST.get('Body')
            digits = ''.join(filter(str.isdigit, from_phone))
            if len(digits) == 10:
                from_phone =  f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
            elif len(digits) == 11:
                from_phone =  f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
            else:
                return HttpResponse(f"from-Phone must be 10 (or 11) digits ({digits})", status=405)

            digits = ''.join(filter(str.isdigit, to_phone))
            if len(digits) == 10:
                to_phone =  f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
            elif len(digits) == 11:
                to_phone =  f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
            else:
                return HttpResponse(f"to-Phone must be 10 (or 11) digits ({digits})", status=405)


            #process_sms_message(to_phone, from_phone, user_input)
            process_sms_message.delay(to_phone, from_phone, user_input)

            sms_resp = MessagingResponse()

            return HttpResponse(sms_resp, status=200)
        else:
            return HttpResponse('Method not allowed', status=405)
    else:
        return HttpResponse('Method not allowed', status=405)


@csrf_exempt  # Disable CSRF protection for this view
def smsweb_receiver(request):
    if request.method == 'POST':
        # Get the full request URL

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        from_phone = request.POST.get('From')
        to_phone = request.POST.get('To')
        user_input = request.POST.get('Body')
        digits = ''.join(filter(str.isdigit, from_phone))
        if len(digits) == 10:
            from_phone =  f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11:
            from_phone =  f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
        else:
            return HttpResponse(f"from-Phone must be 10 (or 11) digits ({digits})", status=405)

        digits = ''.join(filter(str.isdigit, to_phone))
        if len(digits) == 10:
            to_phone =  f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11:
            to_phone =  f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
        else:
            return HttpResponse(f"to-Phone must be 10 (or 11) digits ({digits})", status=405)
        c = SMSConversationManager(temperature=0.0, model_name="gpt-4-0125-preview")
        # c = SMSConversationManager(temperature=0.0, model_name="gpt-4-1106-preview")
        response = c.respond_to_input(from_phone, to_phone, user_input)
        userId = c.assistant.msg_user.id
        serverMsgId = c.server_msgId
        userMsgId = c.user_msgId
        # Construct the JSON response
        data = {
            'output': response['output'],
            'userId': userId,
            'serverMsgId': serverMsgId,
            'previousMsgId': userMsgId
        }

        return JsonResponse(data)
    else:
        return HttpResponse('Method not allowed', status=405)

@csrf_exempt  # Disable CSRF protection for this view
def mark_sms_message(request):
    if request.method == 'POST':
        data = request.POST
        sms_marked_message = SMSMarkedMessage.objects.create(
            message_id=data['message_id'],
            preceding_message_id=data['previousmsgid'],
            comment=data['comment']
        )
        return JsonResponse({'status': 'success', 'sms_marked_message_id': sms_marked_message.id})
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

def is_from_followupboss(context, signature, system_key):
    # Encode the context (payload) using base64
    encoded_context = base64.b64encode(context.encode('utf-8'))

    # Create a SHA256 hash with the base64 encoded value and the system key
    calculated_signature = hmac.new(system_key.encode('utf-8'), encoded_context, hashlib.sha256).hexdigest()

    # Compare the calculated signature with the received signature
    return signature == calculated_signature

# The handler function is temporary to capture some calls
@csrf_exempt
def fubhook_handler(request, event_type):
    if request.method == 'POST':
        input_data = json.loads(request.body)
        json_payload = request.body.decode('utf-8')
        event_id = input_data['eventId']
        event = input_data['event']
        resource_uri = input_data['uri']
        system_key = os.getenv('FUB_X_SYSTEM_KEY')
        signature_from_header = request.headers.get('FUB-Signature')

        if not input_data or not signature_from_header:
            logger.error('Webhook data or signature missing')
            return JsonResponse({'error': 'Webhook data or signature missing'}, status=400)

        try:
            if is_from_followupboss(json_payload, signature_from_header, system_key):
                FUBhookEvent.objects.create(event_type=event_type, data=input_data)
                return JsonResponse({'message': 'Webhook received and verified successfully'}, status=200)
            else:
                logger.error('Failed to verify webhook signature')
                return JsonResponse({'error': 'Unauthorized'}, status=401)
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return JsonResponse({'error': 'Internal server error'}, status=500)
        else:
            logger.error('Invalid request method')
            return JsonResponse({'error': 'Invalid request method'}, status=400)



