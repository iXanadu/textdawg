from django.contrib import admin
from .models import FUBMessageUser, FubMessageHistory,TextCode,ChatMessage,ChatTopic,UserProfile,OpenAIPrompt

# Register your models here.
admin.site.register(FUBMessageUser)
admin.site.register(FubMessageHistory)
admin.site.register(TextCode)
admin.site.register(ChatMessage)
admin.site.register(ChatTopic)
admin.site.register(UserProfile)
admin.site.register(OpenAIPrompt)

# Register your models here.
