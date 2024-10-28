from django.contrib import admin
from .models import *
admin.site.register(Agent)
admin.site.register(Voice)
admin.site.register(Phone_Number)
admin.site.register(CustomUser)
admin.site.register(CallHistory)
# Register your models here.
