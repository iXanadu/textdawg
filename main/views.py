import logging
import re
from django.core import serializers
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .models import OpenAIPrompt, SMSMarkedMessage,FubMessageHistory
from django.apps import apps
import json

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