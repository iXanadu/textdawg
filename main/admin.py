from django.contrib import admin
from .models import FUBMessageUser, FubMessageHistory,TextCode,ChatMessage,ChatTopic,UserProfile

# Register your models here.
admin.site.register(FUBMessageUser)
admin.site.register(FubMessageHistory)
admin.site.register(TextCode)
admin.site.register(ChatMessage)
admin.site.register(ChatTopic)
admin.site.register(UserProfile)

# Register your models here.
