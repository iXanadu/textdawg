import logging
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from main.models import ChatTopic, ChatMessage
from messenger.sms_conversation_manager import SMSConversationManager
from messenger.gpt_conversation_manager import GPTConversationManager

logger = logging.getLogger(__name__)
# sms_client = Client(os.getenv('MY_ACCOUNT_SID'),os.getenv('TWILIO_AUTH_TOKEN'))

@require_POST
def create_chat_topic(request):
    topic_text = request.POST.get('topic')
    topic, created = ChatTopic.objects.get_or_create(user=request.user, topic_text=topic_text)
    return JsonResponse({'topic_id': topic.id, 'topic_text': topic.topic_text, 'created': created})

@login_required
@require_GET
def list_chat_topics(request):
    topics = ChatTopic.objects.filter(user=request.user).values('id', 'topic_text')
    return JsonResponse(list(topics), safe=False)

@login_required
@require_GET
def get_chat_messages(request, topic_id):
    messages = ChatMessage.objects.filter(topic_id=topic_id).order_by('timestamp').values('message_text', 'role',
                                                                                          'timestamp')
    return JsonResponse(list(messages), safe=False)


@csrf_exempt  # Disable CSRF protection for this view
def chat_receiver(request):
    if request.method == 'POST':
        print(f"chat_receiver-Request={request}")
        user_input = request.POST.get('Body')
        print(user_input)
        c = GPTConversationManager(temperature=0.0, model_name="gpt-4-1106-preview")
        print(c)
        response = c.respond_to_input(user_input)
        print(response)
        return HttpResponse(response['output'], status=200)
    else:
        return HttpResponse('Method not allowed', status=405)


@csrf_exempt  # Disable CSRF protection for this view
def sms_receiver(request):
    if request.method == 'POST':
        print("In sms_receiver, request=({reqest})")
        from_phone = request.POST.get('From')
        to_phone = request.POST.get('To')
        user_input = request.POST.get('Body')
        digits = ''.join(filter(str.isdigit, from_phone))
        if len(digits) == 10:
            from_phone =  f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        elif len(digits) == 11:
            from_phone =  f"{digits[1:4]}-{digits[4:7]}-{digits[7:11]}"
        else:
            return HttpResponse(f"Phone must be 10 (or 11) digits ({digits})", status=200)

        c = SMSConversationManager(temperature=0.0, model_name="gpt-4-1106-preview")
        response = c.respond_to_input(from_phone, user_input)

        return HttpResponse(response['output'], status=200)
    else:
        return HttpResponse('Method not allowed', status=405)


