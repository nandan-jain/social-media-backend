from django.contrib import admin
from core.models.user import User
from core.models.request import Request

# Register your models here.
admin.site.register(User)
admin.site.register(Request)

