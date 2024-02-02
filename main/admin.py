from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import (FUBMessageUser, FubMessageHistory,TextCode,ChatMessage,
                     ChatTopic,UserProfile,OpenAIPrompt,SMSMarkedMessage, FubWebhook)
from .forms import FUBMessageUserAdminForm

# Register your models here.
# admin.site.register(FUBMessageUser)
admin.site.register(FubMessageHistory)
admin.site.register(TextCode)
admin.site.register(ChatMessage)
admin.site.register(ChatTopic)
admin.site.register(UserProfile)
admin.site.register(OpenAIPrompt)
admin.site.register(SMSMarkedMessage)
admin.site.register(FubWebhook)


class FUBMessageUserAdmin(admin.ModelAdmin):
    form = FUBMessageUserAdminForm
    # Optional: You can define list_display, search_fields, etc., here.

admin.site.register(FUBMessageUser, FUBMessageUserAdmin)
