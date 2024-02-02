import logging
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

class FUBMessageUser(models.Model):
    fubId = models.IntegerField(unique=True)
    phone_number = models.CharField(max_length=50, unique=True)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField()
    message_count = models.IntegerField(default=0)
    is_opted_out = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['fubId', 'phone_number'], name='unique_fubId_phone')
        ]
    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.phone_number}"

class FubMessageHistory(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    fubId = models.IntegerField()
    phone_number = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=[('Human', 'Human'), ('AI', 'AI'), ('System', 'System')])
    message = models.TextField()
    status = models.CharField(max_length=100)

    # Foreign Key to MessageUser
    message_user = models.ForeignKey(FUBMessageUser, on_delete=models.CASCADE, related_name='message_history')
    def __str__(self):
        return f"Message on {self.timestamp} by {self.role}"


class TextCode(models.Model):
    textcode = models.CharField(max_length=255,unique=True)
    link = models.CharField(max_length=255)
    property_address = models.CharField(max_length=255)
    instructions = models.TextField(max_length=255)

    def __str__(self):
        return f"Textcode {self.textcode} => {self.link}"

class ChatTopic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics')
    topic_text = models.CharField(max_length=255)

    class Meta:
        unique_together = ('user', 'topic_text')

    def __str__(self):
        return f"{self.topic_text} by {self.user.username}"

class ChatMessage(models.Model):
    topic = models.ForeignKey(ChatTopic, on_delete=models.CASCADE, related_name='messages')
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=10, choices=[('Human', 'Human'), ('AI', 'AI')])

    def __str__(self):
        return f"{self.role} message in {self.topic.topic_text} at {self.timestamp}"

    from django.db import models


class OpenAIPrompt(models.Model):
    key = models.CharField(max_length=255)
    prompt_text = models.TextField()
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    isActive = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=1)
    variables = models.TextField(blank=True, null=True)  # A comma-separated list of variable names

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['key', 'version'], name='unique_key_version')
        ]

    @classmethod
    def get_active_prompt(cls, key):
        try:
            prompts = cls.objects.filter(key=key).order_by('-version')
            # logger.info(f"Found {prompts.count()} prompts with key '{key}'.")

            for prompt in prompts:
                # logger.info(f"Checking prompt: {prompt.key}, Version: {prompt.version}, IsActive: {prompt.isActive}")
                if prompt.isActive or prompts.count() == 1:
                    # logger.info(f"Returning active prompt: {prompt}")
                    return prompt

            logger.warning(f"No active prompt found for key '{key}'.")
            return None

        except Exception as e:
            logger.error(f"Error in get_active_prompt: {str(e)}")
            return None

    def __str__(self):
        return f"{self.key} (Version {self.version})"

class SMSMarkedMessage(models.Model):
    message_id = models.IntegerField()  # ID of the marked server response
    preceding_message_id = models.IntegerField()  # ID of the preceding human message
    comment = models.TextField()  # User's comment on the server response
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp of marking the message
    resolved = models.BooleanField(default=False)  # Defaulting to False indicating unresolved

    def __str__(self):
        return f"SMS Marked Message {self.message_id}"

class FUBhookEvent(models.Model):
    event_type = models.CharField(max_length=50)
    data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} - {self.created_at}"


class FubWebhook(models.Model):
    webhookId = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=50)
    event = models.CharField(max_length=100)
    url = models.URLField(max_length=200)

    def __str__(self):
        return f"Webhook {self.event} - {self.status}"