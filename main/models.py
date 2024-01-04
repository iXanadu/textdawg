from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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
