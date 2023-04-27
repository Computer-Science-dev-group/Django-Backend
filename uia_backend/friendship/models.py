from django.db import models
from uia_backend.accounts.models import CustomUser

# Create your models here.

class FriendsRelationship(models.Model):
    INVITE_STATUS = (
        ("pending", "pending"),
        ("accepted", "accepted"),
        ("rejected", "rejected"),
    )
    
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="receiver")
    is_friend = models.BooleanField(default=False)
    invite_status = models.CharField(max_length=10, choices=INVITE_STATUS,default="pending")
    is_blocked = models.BooleanField(default=False)


    def __str__(self):
        return f"Friend Request from {self.sender} to {self.receiver}"

