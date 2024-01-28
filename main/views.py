import logging
import re
from django.core import serializers
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .models import OpenAIPrompt
import json

logger = logging.getLogger(__name__)

@login_required(login_url='/login/')
def dashboard(request):
    return render(request, 'main/dashboard.html')

# Other views...

@login_required(login_url='/login/')
def prompt_management(request):
    return render(request, 'main/prompt_management.html')

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


def prompt_add(request):
    try:
        if request.method == 'POST':
            data = json.loads(request.body)
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
        return HttpResponseBadRequest(json.dumps({'error': e.messages}))
    except KeyError:
        return HttpResponseBadRequest(json.dumps({'error': 'Missing required fields'}))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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


def prompt_get_full_prompt(request, id):
    try:
        if request.method == 'GET':
            prompt = OpenAIPrompt.objects.get(id=id)
            return JsonResponse({'prompt_text': prompt.prompt_text})
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Prompt not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

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
