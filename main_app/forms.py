# rentals/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from .models import USBDevice, RentalRequest, UserPC, Manufacturer, ManufacturerWhitelist

class USBDeviceForm(forms.ModelForm):
    class Meta:
        model = USBDevice
        fields = ['name', 'description', 'manufacturer', 'purchase_date', 'capacity']
        labels = {
            'name': 'デバイス名',
            'description': '説明',
            'manufacturer': 'メーカー',
            'purchase_date': '購入日',
            'capacity': '容量（バイト数）',
        }
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'capacity': forms.NumberInput(attrs={'min': 0, 'step': 1}),
        }
        error_messages = {
            'name': {
                'unique': "この名前のUSBデバイスは既に登録されています。",
            },
        }

class UserPCForm(forms.ModelForm):
    class Meta:
        model = UserPC
        fields = ['serial_number', 'antivirus_version']
        labels = {
            'serial_number': 'PCの製品番号',
            'antivirus_version': 'ウイルス対策のバージョン',
        }
        widgets = {
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'antivirus_version': forms.TextInput(attrs={'class': 'form-control'}),
        }

class RentalRequestForm(forms.ModelForm):
    class Meta:
        model = RentalRequest
        fields = ['start_date', 'end_date', 'approver', 'pc']
        labels = {
            'start_date': 'レンタル開始日',
            'end_date': '返却日',
            'approver': '承認者',
            'pc': '利用PC',
        }
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pc'].queryset = UserPC.objects.filter(user=user)
            
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        # 開始日が返却日よりも後になっていないかチェック
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', "返却日は開始日より後の日付を選択してください。")
        
class ReturnRequestForm(forms.Form):
    comments = forms.CharField(
        label="返却時のコメント", 
        widget=forms.Textarea, 
        required=False,
        help_text="任意で返却に関するコメントを記入してください。"
    )

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="ユーザー名",
        help_text="150文字以下。文字、数字、@/./+/-/_ のみ使用可能。",
        error_messages={
            'required': "ユーザー名を入力してください。",
            'unique': "このユーザー名は既に使用されています。他の名前をお試しください。",
        }
    )
    email = forms.EmailField(
        required=True,
        label="メールアドレス",
        help_text="有効なメールアドレスを入力してください。",
    )
    password1 = forms.CharField(
        label="パスワード",
        widget=forms.PasswordInput,
        help_text="8文字以上のパスワードを入力してください。",
        error_messages={
            'required': "パスワードを入力してください。",
        }
    )
    password2 = forms.CharField(
        label="パスワード（確認用）",
        widget=forms.PasswordInput,
        help_text="確認のため、同じパスワードをもう一度入力してください。",
        error_messages={
            'required': "確認用パスワードを入力してください。",
        }
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
    
        

class ManufacturerForm(forms.ModelForm):
    class Meta:
        model = Manufacturer
        fields = ['name']
        labels = {
            'name': 'メーカー名',
        }
        
class ManufacturerWhitelistForm(forms.ModelForm):
    class Meta:
        model = ManufacturerWhitelist
        fields = ['manufacturer']
        labels = {
            'manufacturer': 'メーカー',
        }
        widgets = {
            'manufacturer': forms.Select(attrs={'class': 'form-control'}),
        }
        
class ExtensionRequestForm(forms.ModelForm):
    new_end_date = forms.DateField(
        label="新しい返却期日",
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    class Meta:
        model = RentalRequest
        fields = ['new_end_date']

    def clean_new_end_date(self):
        new_end_date = self.cleaned_data.get('new_end_date')
        if new_end_date <= timezone.now().date():
            raise forms.ValidationError("返却期日は今日以降の日付を指定してください。")
        return new_end_date
    