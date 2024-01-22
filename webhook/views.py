import logging
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from main.models import ChatTopic, ChatMessage
from messenger.gpt_conversation_manager import GPTConversationManager
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from .sms_tasks import process_sms_message


import os


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
    print(request.GET)
    print(f"topic_id:{topic_id}")

    messages = ChatMessage.objects.all().values('message_text', 'role', 'timestamp', 'topic_id')
    print (messages)
    response = JsonResponse(list(messages), safe=False)
    print(response)

    messages = ChatMessage.objects.filter(topic_id=topic_id).order_by('timestamp').values('message_text', 'role',
                                                                                          'timestamp')
    print (messages)
    response = JsonResponse(list(messages), safe=False)
    print (response)
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

        logger.info(f"In sms_receiver POST is {request.POST}")
        # Get the full request URL
        url = 'http://textdawg.com/webhook/sms_receiver/'

        # Get the POST data and headers
        post_vars = request.POST
        twilio_signature = request.headers.get('X-Twilio-Signature')

        # Create an instance of the RequestValidator
        validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))

        logger.info(f"Passed validator")

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


            logger.info(f"Calling process_sms_message.delay with {to_phone}, {from_phone}, {user_input}")
            
            #process_sms_message(to_phone, from_phone, user_input)
            process_sms_message.delay(to_phone, from_phone, user_input)

            sms_resp = MessagingResponse()
            logger.info(f"Returning sms_resp: {sms_resp}")

            return HttpResponse(sms_resp, status=200)
        else:
            return HttpResponse('Method not allowed', status=405)
    else:
        return HttpResponse('Method not allowed', status=405)


