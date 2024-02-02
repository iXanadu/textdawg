import logging
import re
import requests
from django.core import serializers
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt,csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .models import OpenAIPrompt, SMSMarkedMessage,FubMessageHistory,FubWebhook
from crm.fub_api_handler import FUBApiHandler
from django.apps import apps
import json
import os

logger = logging.getLogger(__name__)

@login_required(login_url='/login/')
def index(request):
    return render(request, 'main/index.html')
@login_required(login_url='/login/')
def dashboard(request):
    return render(request, 'main/dashboard.html')

# Other views...
@login_required
def get_model_permissions(request):
    if request.method == 'POST':
        try:
            model_names = json.loads(request.body).get('models', [])
            permissions = {}

            # Ensure model_names is always a list
            if not isinstance(model_names, list):
                model_names = model_names.split(',')

            for model_name in model_names:
                model_name = model_name.strip()  # Remove any leading/trailing spaces
                if not model_name:
                    continue  # Skip empty model names

                model = apps.get_model('main', model_name)
                permissions[model_name] = {
                    'can_add': request.user.has_perm(f'{model._meta.app_label}.add_{model._meta.model_name}'),
                    'can_change': request.user.has_perm(f'{model._meta.app_label}.change_{model._meta.model_name}'),
                    'can_delete': request.user.has_perm(f'{model._meta.app_label}.delete_{model._meta.model_name}'),
                    'can_view': request.user.has_perm(f'{model._meta.app_label}.view_{model._meta.model_name}'),
                }


            return JsonResponse(permissions)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def fub_webhooks(request):
    return render(request, 'main/fub_webhook.html')



@login_required(login_url='/login/')
def prompt_management(request):
    return render(request, 'main/prompt_management.html')

@login_required
def prompt_list(request):
    try:
        if request.method == 'GET':
            sort_column = request.GET.get('sort_column', 'default_column')
            sort_direction = request.GET.get('sort_direction', 'asc')

            if sort_direction == 'desc':
                sort_column = '-' + sort_column

            prompts = OpenAIPrompt.objects.all().order_by(sort_column)

            # Serialize the queryset
            data = serializers.serialize('json', prompts)
            return JsonResponse(data, safe=False, content_type='application/json')

    except Exception as e:
        logger.error(f"Error in prompt_list: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def prompt_add(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            logger.info(data)
            prompt_text = data['prompt_text']
            # Regex to find patterns like {variable}
            variables = re.findall(r'\{([^\}]+)\}', prompt_text)
            variable_list = ','.join(variables)
            # Convert 'version' to integer
            version = int(data.get('version', 1))  # Default to 1 if not provided

            # Convert 'isActive' to boolean
            isactive = data.get('is_active', False)

            prompt = OpenAIPrompt.objects.create(
                key=data['key'],
                prompt_text=prompt_text,
                description = data['description'],
                category = data['category'],
                isActive = isactive,
                version = version,
                variables=variable_list
                # add other fields as necessary
            )
            return JsonResponse({'id': prompt.id})
    except ValidationError as e:
        logger.error(f"Validation Error: {e}")
        return HttpResponseBadRequest(json.dumps({'error': e.messages}))
    except KeyError as e:
        logger.error(f"Key Error: {e}")
        return HttpResponseBadRequest(json.dumps({'error': 'Missing required fields'}))
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        return JsonResponse({'error': str(e)}, status=500)
@login_required
def prompt_edit(request, id):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            prompt = OpenAIPrompt.objects.get(id=id)

            # Update prompt fields with new data
            prompt.key = data['key']
            prompt.prompt_text = data['prompt_text']
            prompt.description = data.get('description', '')
            prompt.category = data.get('category', '')

            # Regex to find patterns like {variable}
            variables = re.findall(r'\{([^\}]+)\}', prompt.prompt_text)
            prompt.variables = ','.join(variables)

            # Convert 'version' to integer and 'isActive' to boolean
            prompt.version = int(data.get('version', 1))
            prompt.isActive = data.get('is_active', False)

            prompt.save()
            return JsonResponse({'id': prompt.id})
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Prompt not found'}, status=404)
    except KeyError:
        return HttpResponseBadRequest(json.dumps({'error': 'Missing required fields'}))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def prompt_get_full_prompt(request, id):
    try:
        if request.method == 'GET':
            prompt = OpenAIPrompt.objects.get(id=id)
            return JsonResponse({'prompt_text': prompt.prompt_text})
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Prompt not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def prompt_delete(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            ids_to_delete = data['promptIds']

            # Convert the string of IDs into a list of integers
            ids_list = [int(id.strip()) for id in ids_to_delete if id.strip().isdigit()]

            # Delete prompts with the given IDs
            OpenAIPrompt.objects.filter(id__in=ids_list).delete()
            return JsonResponse({'status': 'success'})
    except KeyError as e:
        logger.error(f"KeyError in prompt_delete: Missing key {str(e)}")
        return HttpResponseBadRequest(json.dumps({'error': 'Missing required fields'}))
    except Exception as e:
        logger.error(f"Error in prompt_delete: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required(login_url='/login/')
def audit_messages(request):
    return render(request, 'main/audit_messages.html')

@login_required
def audit_get_messages(request):
    if request.method == 'GET':
        marked_messages = SMSMarkedMessage.objects.all().order_by('-created_at')
        marked_messages_data = []

        for marked_message in marked_messages:
            try:
                server_message = FubMessageHistory.objects.get(id=marked_message.message_id).message
            except FubMessageHistory.DoesNotExist:
                server_message = "Message not found or deleted"

            marked_messages_data.append({
                'pk': marked_message.id,
                'created_at': marked_message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                'comment': marked_message.comment,
                'server_message': server_message,
                'resolved': marked_message.resolved
            })

        # Convert the list of dictionaries to JSON string
        data = json.dumps(marked_messages_data)

        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def audit_get_message(request, message_id):
    if request.method == 'GET':
        try:
            message = SMSMarkedMessage.objects.get(id=message_id)
            conversation_data = get_audit_conversation(message)
            return JsonResponse(conversation_data)
        except SMSMarkedMessage.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
def get_audit_conversation(message):
    marked_message = message
    print(message)
    try:
        server_message = FubMessageHistory.objects.get(id=marked_message.message_id).message
    except FubMessageHistory.DoesNotExist:
        server_message = "Message not found or deleted"
    try:
        preceding_user_message = FubMessageHistory.objects.get(id=marked_message.preceding_message_id).message
    except FubMessageHistory.DoesNotExist:
        preceding_user_message  = "Message not found or deleted"

    conversation_data = {
        'server_message': server_message,
        'preceding_user_message': preceding_user_message
    }
    return (conversation_data)

@login_required
def audit_resolve_message(request):
    if request.method == 'POST':
        try:
            message_id = request.POST.get('message_id')
            resolved_status = request.POST.get('resolved_status') == 'true'  # Convert to boolean

            message = SMSMarkedMessage.objects.get(id=message_id)
            message.resolved = resolved_status
            message.save()

            return JsonResponse({'status': 'success'})
        except SMSMarkedMessage.DoesNotExist:
            return JsonResponse({'error': 'Message not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def audit_delete_messages(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
            ids_to_delete = data['messageIds']

            # Convert the string of IDs into a list of integers
            ids_list = [int(id.strip()) for id in ids_to_delete if id.strip().isdigit()]

            # Delete prompts with the given IDs
            SMSMarkedMessage.objects.filter(id__in=ids_list).delete()
            return JsonResponse({'status': 'success'})
    except KeyError as e:
        logger.error(f"KeyError in prompt_delete: Missing key {str(e)}")
        return HttpResponseBadRequest(json.dumps({'error': 'Missing required fields'}))
    except Exception as e:
        logger.error(f"Error in prompt_delete: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@csrf_protect
def fub_webhook_register(request):
    if request.method == 'POST':
        data = request.POST
        event = data.get('event')
        url = data.get('url')
        # Initialize your FUB API handler here
        fub_handler = FUBApiHandler(os.getenv('FUB_API_URL'), os.getenv('FUB_API_KEY'),
                                    os.getenv('FUB_X_SYSTEM'), os.getenv('FUB_X_SYSTEM_KEY'))

        # Attempt to register the webhook with the external API
        api_response = fub_handler._make_request('POST', '/v1/webhooks', data={'event': event, 'url': url})
        if api_response and 'id' in api_response:
            webhook, created = FubWebhook.objects.get_or_create(event=event, defaults={'url': url, 'webhookId': api_response['id']})
            if not created:
                webhook.webhookId = api_response['id']
                webhook.url = url
                webhook.status = 'Active'
                webhook.save()
                logger.info(f"Webhook for {event} updated successfully with webhook ID {api_response['id']}.")
            else:
                logger.info(f"Webhook for {event} registered successfully with webhook ID {api_response['id']}.")
            return JsonResponse({'message': 'Webhook registered successfully.', 'webhookId': api_response['id']}, status=200)
        else:
            logger.error(f"Failed to register webhook for {event}. API response: {api_response}")
            return JsonResponse({'error': 'Failed to register webhook with the external API.'}, status=500)
    else:
        logger.error("Invalid request method used for fub_webhook_register.")
        return JsonResponse({'error': 'Invalid request method.'}, status=400)
@login_required
def fub_webhook_deregister(request, webhook_id):
    fub_handler = FUBApiHandler(os.getenv('FUB_API_URL'), os.getenv('FUB_API_KEY'),
                                os.getenv('FUB_X_SYSTEM'), os.getenv('FUB_X_SYSTEM_KEY'))
    try:
        # Attempt to retrieve the webhook from your database
        webhook = FubWebhook.objects.get(id=webhook_id)
    except FubWebhook.DoesNotExist:
        # Log and respond if the webhook does not exist
        logger.error(f"Webhook with ID {webhook_id} not found.")
        return JsonResponse({'error': 'Webhook not found.'}, status=404)

    try:
        # Proceed with the API call to deregister
        api_response = fub_handler._make_request('DELETE', f'/v1/webhooks/{webhook_id}')
        if api_response is None:
            logger.error(f"Failed to deregister webhook with ID {webhook_id}")
            return JsonResponse({'error': 'API call to deregister webhook failed.'}, status=500)

        # Successfully deregistered, now delete or update the status in the database
        webhook.delete()  # Or set status to 'inactive', depending on the requirement
        return JsonResponse({'message': 'Webhook deregistered successfully.'}, status=200)
    except Exception as e:
        # Log any other exceptions that occur during the deregistration process
        logger.exception(f"Error deregistering webhook: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)

@login_required
def fub_webhook_list(request):
    try:
        # Retrieve all webhook records from the database
        webhooks = FubWebhook.objects.all().values('id', 'webhookId','status', 'event', 'url')
        # Convert the QuerySet to a list of dictionaries
        webhooks_list = list(webhooks)
        return JsonResponse({'webhooks': webhooks_list}, status=200)
    except Exception as e:
        # Log the error and return an error response
        logger.error(f"Failed to retrieve webhooks: {e}")
        return JsonResponse({'error': 'An unexpected error occurred while retrieving webhooks.'}, status=500)

@login_required
def fub_webhook_delete(request, id):
    fub_handler = FUBApiHandler(os.getenv('FUB_API_URL'), os.getenv('FUB_API_KEY'),
                                os.getenv('FUB_X_SYSTEM'), os.getenv('FUB_X_SYSTEM_KEY'))
    try:
        # Retrieve the webhook to be deleted
        webhook = FubWebhook.objects.get(id=id)
    except FubWebhook.DoesNotExist:
        logger.error(f"Webhook with ID {id} not found in the database.")
        return JsonResponse({'error': 'Webhook not found.'}, status=404)

    webhook_id = webhook.webhookId
    # Attempt to deregister the webhook via the API
    api_response = fub_handler._make_request('DELETE', f'/v1/webhooks/{webhook_id}')
    if api_response is None:
        logger.error(f"Failed to deregister webhook with ID {webhook_id} via the API.")
        return JsonResponse({'error': 'Failed to deregister webhook via the API.'}, status=500)

    # Delete the webhook from the database
    try:
        webhook.delete()
    except Exception as e:
        logger.exception(f"Failed to delete webhook with ID {webhook_id} from the database: {e}")
        return JsonResponse({'error': 'Failed to delete webhook from the database.'}, status=500)

    return JsonResponse({'message': 'Webhook deleted successfully.'}, status=200)

@login_required
def fub_webhook_change(request, id):
    fub_handler = FUBApiHandler(os.getenv('FUB_API_URL'), os.getenv('FUB_API_KEY'),
                                os.getenv('FUB_X_SYSTEM'), os.getenv('FUB_X_SYSTEM_KEY'))
    if request.method == 'POST':
        try:
            # Retrieve the existing webhook entry
            webhook = FubWebhook.objects.get(id=id)
        except FubWebhook.DoesNotExist:
            logger.error(f"Webhook with ID {webhook_id} not found.")
            return JsonResponse({'error': 'Webhook not found.'}, status=404)

        # Extract the new URL from the request
        new_url = request.POST.get('url')

        # Prepare data for API update
        data = {
            'url': new_url,  # Update only the URL since the event remains the same
        }

        # Make the API call to update the webhook
        api_response = fub_handler._make_request('PUT', f'/v1/webhooks/{webhook_id}', data=data)
        if api_response is None:
            logger.error(f"Failed to update webhook with ID {webhook_id} via the API.")
            return JsonResponse({'error': 'Failed to update webhook via the API.'}, status=500)

        # Update the webhook URL in the database
        try:
            webhook.url = new_url
            webhook.save()
        except Exception as e:
            logger.exception(f"Failed to update webhook with ID {webhook_id} in the database: {e}")
            return JsonResponse({'error': 'Failed to update webhook in the database.'}, status=500)

        return JsonResponse({'message': 'Webhook URL updated successfully.'}, status=200)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def fub_webhook_get(request, id):
    try:
        webhook = FubWebhook.objects.get(id=id)
        return JsonResponse({
            'id': webhook.id,
            'webhookId':webhook.webhookId,
            'status': webhook.status,
            'event': webhook.event,
            'url': webhook.url,
        }, status=200)
    except FubWebhook.DoesNotExist:
        return JsonResponse({'error': 'Webhook not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error retrieving webhook: {e}")
        return JsonResponse({'error': 'An unexpected error occurred.'}, status=500)




