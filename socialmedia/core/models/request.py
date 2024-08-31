from django.db import models
from .user import User

class Request(models.Model):
    STATUS_CHOICES = (
        ("sent", "sent"),
        ("accepted", "accepted"),
        ("rejected", "rejected"),

    )

    from_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="sent_requests")
    to_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="received_requests")
    status = models.CharField(choices=STATUS_CHOICES, max_length=8)

    def __str__(self):
        return f"Request from {self.from_user.name} to {self.to_user.name} - Status: {self.status}"

    