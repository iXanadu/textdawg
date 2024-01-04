from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
import os
import json
from messenger.sms_conversation_manager import SMSConversationManager
from crm.fub_api_handler import FUBApiHandler
import csv

@login_required(login_url='/login/')
def textbot_view(request):
    phone_number = request.user.userprofile.phone_number
    email = request.user.email

    context = {
        'phone_number': phone_number,
        'email': email,
        # ... other context variables ...
    }
    return render(request, 'webhook_lab/textbot.html',context)

@login_required(login_url='/login/')
def chatbot_view(request):
    phone_number = request.user.userprofile.phone_number
    user_id = request.user.id
    email = request.user.email

    context = {
        'user_id': user_id,
        'phone_number': phone_number,
        'email': email,
        # ... other context variables ...
    }

    return render(request, 'webhook_lab/chatbot.html', context)

def test_ai_assistant(request):
    # assistant = AIBaseAssistant()
    # response = assistant.respond_to_input('1640')
    # c = SMSConversationManager()
    # response = c.respond_to_input('(757) 632-3156','1640')

    f = FUBApiHandler(os.getenv('FUB_API_URL'), os.getenv('FUB_API_KEY'),
                                os.getenv('FUB_X_SYSTEM'), os.getenv('FUB_X_SYSTEM_KEY'))
    # response = f.get_bulk_text_messages()
    response = f.get_bulk_text_messages()

    # textmessages = response.get('textmessages', [])
    # csv_file_path = 'textmessages.csv'
    # columns_to_include = ['id', 'created', 'updated', 'personId', 'status', 'message', 'fromNumber', 'toNumber', 'sent']
    # with open(csv_file_path, mode='w', newline='') as csv_file:
    #     writer = csv.DictWriter(csv_file, fieldnames=columns_to_include)
    #     writer.writeheader()
    #     for message in textmessages:
    #         row = {col: message[col] for col in columns_to_include}
    #         writer.writerow(row)
    #
    # html_string = f'CSV file saved to {csv_file_path}'
    return render(request, 'webhook_lab/test_template.html', {'response': response})

# Create your views here.
