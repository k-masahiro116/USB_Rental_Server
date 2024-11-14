from django.db import models

# Create your models here.
# rentals/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Manufacturer(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="メーカー名")

    def __str__(self):
        return self.name
    
class ManufacturerWhitelist(models.Model):
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, verbose_name="メーカー")
    added_at = models.DateTimeField(auto_now_add=True, verbose_name="登録日時")

    def __str__(self):
        return f"ホワイトリスト: {self.manufacturer.name}"
    
class USBDevice(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE, null=True, verbose_name="メーカー")
    purchase_date = models.DateField(verbose_name="購入日", null=True, blank=True)
    capacity = models.BigIntegerField(verbose_name="容量（バイト数）", null=True, blank=True)

    def __str__(self):
        return self.name

    def __str__(self):
        return self.name
    
class UserPC(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    serial_number = models.CharField(max_length=100, unique=True, verbose_name="PCの製品番号")
    antivirus_version = models.CharField(max_length=50, verbose_name="ウイルス対策のバージョン")

    def __str__(self):
        return f"{self.user.username} - {self.serial_number}"

class RentalRequest(models.Model):
    usb_device = models.ForeignKey(USBDevice, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    # レンタル開始日と返却日フィールドの追加
    start_date = models.DateField(verbose_name="レンタル開始日", null=True)
    end_date = models.DateField(verbose_name="返却日", null=True)
    
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="approved_requests", verbose_name="承認者")
    pc = models.ForeignKey(UserPC, on_delete=models.SET_NULL, null=True, verbose_name="利用PC")

    is_returned = models.BooleanField(default=False, verbose_name="返却済み")
    @property
    def is_overdue(self):
        """返却期日が過ぎているかどうかを確認する"""
        return self.end_date < timezone.now().date()
    
    def __str__(self):
        return f"{self.user.username} - {self.usb_device.name} - {'返却済み' if self.is_returned else '未返却'}"
    
