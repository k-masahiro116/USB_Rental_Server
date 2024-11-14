from django.contrib import admin

# Register your models here.
from .models import USBDevice, RentalRequest

admin.site.register(USBDevice)
admin.site.register(RentalRequest)