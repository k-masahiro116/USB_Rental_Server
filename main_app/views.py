from django.core.mail import send_mail
from smtplib import SMTPException
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView, ListView, CreateView, FormView, View, DetailView, UpdateView, DeleteView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.utils import timezone
from .models import USBDevice, RentalRequest, UserPC, Manufacturer, ManufacturerWhitelist
from .forms import UserPCForm, USBDeviceForm, RentalRequestForm, ReturnRequestForm, CustomUserCreationForm, ManufacturerForm, ManufacturerWhitelistForm, ExtensionRequestForm

# ホームページや一般的な表示用ビュー
class IndexView(TemplateView):
    template_name = "index.html"

# サインアップビュー
class SignupView(FormView):
    template_name = 'registration/signup.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('index')  # サインアップ後にリダイレクト

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

# USBデバイス登録ビュー
class USBDeviceCreateView(LoginRequiredMixin, CreateView):
    model = USBDevice
    form_class = USBDeviceForm
    template_name = 'rentals/usb_device_form.html'
    success_url = reverse_lazy('usb_list')  # 登録後に一覧ページにリダイレクト

    def form_valid(self, form):
        # 必要であれば、保存処理前の処理をここに追加
        return super().form_valid(form)

class USBDeviceDetailView(LoginRequiredMixin, DetailView):
    model = USBDevice
    template_name = 'rentals/usb_device_detail.html'
    context_object_name = 'usb_device'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 現在レンタル中の情報を取得（所有者とレンタル期間）
        current_rental = RentalRequest.objects.filter(
            usb_device=self.object, is_returned=False
        ).first()
        
        # レンタル履歴を取得（新しい順に並べ替え）
        rental_history = RentalRequest.objects.filter(usb_device=self.object).order_by('-start_date')

        context['current_rental'] = current_rental  # 現在のレンタル情報を追加
        context['rental_history'] = rental_history  # レンタル履歴を追加
        return context
    
    
class USBDeviceUpdateView(LoginRequiredMixin, UpdateView):
    model = USBDevice
    form_class = USBDeviceForm
    template_name = 'rentals/usb_device_update.html'
    success_url = reverse_lazy('usb_list')  # 編集完了後にリダイレクトするページ
    
class USBDeviceDeleteView(LoginRequiredMixin, DeleteView):
    model = USBDevice
    template_name = 'rentals/usb_device_confirm_delete.html'
    success_url = reverse_lazy('usb_list')  # 削除完了後にリダイレクトするページ

# USBデバイス一覧ビュー
class USBListView(LoginRequiredMixin, ListView):
    model = USBDevice
    template_name = 'rentals/usb_list.html'
    context_object_name = 'usb_devices'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ログインユーザーの返却期限が過ぎたレンタルリクエストを取得
        overdue_rentals = RentalRequest.objects.filter(user=self.request.user, end_date__lt=timezone.now().date(), usb_device__is_available=False)
        
        # 期限切れのレンタルリストをコンテキストに追加
        context['overdue_rentals'] = overdue_rentals
        return context
    
class ReturnUSBView(LoginRequiredMixin, FormView):
    template_name = 'rentals/return_request_form.html'
    model = USBDevice
    context_object_name = 'usb_device'
    form_class = ReturnRequestForm
    
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        # object = self.get_object()
        usb_device = self.model.objects.get(id=self.kwargs["usb_id"])
        context["usb_device"] = usb_device
        return context

    def form_valid(self, form):
        # USBデバイスIDを取得
        usb_id = self.kwargs['usb_id']
        usb_device = get_object_or_404(USBDevice, id=usb_id, is_available=False)

        # レンタル申請を取得して返却済みに設定
        rental_request = RentalRequest.objects.filter(usb_device=usb_device, user=self.request.user, is_returned=False).first()
        if rental_request:
            rental_request.is_returned = True
            rental_request.save()

        # USBデバイスを利用可能状態に更新
        usb_device.is_available = True
        usb_device.save()

        # フォームの入力内容を処理
        comments = form.cleaned_data.get('comments')
        # 追加の処理が必要であればここに追加します

        # USBデバイス一覧ページにリダイレクト
        return redirect('usb_list')


class RequestRentalView(LoginRequiredMixin, FormView):
    template_name = 'rentals/request_rental_form.html'
    form_class = RentalRequestForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user  # 現在のユーザーをフォームに渡す
        return kwargs

    def form_valid(self, form):
        usb_id = self.kwargs['usb_id']
        usb_device = get_object_or_404(USBDevice, id=usb_id, is_available=True)

        rental_request = form.save(commit=False)
        rental_request.usb_device = usb_device
        rental_request.user = self.request.user
        rental_request.save()

        usb_device.is_available = False
        usb_device.save()

        return redirect('usb_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usb_device'] = USBDevice.objects.get(id=self.kwargs['usb_id'])
        return context
    
    def post(self, request, usb_id):
        usb_device = get_object_or_404(USBDevice, id=usb_id, is_available=True)
        form = RentalRequestForm(request.POST)
        
        if form.is_valid():
            rental_request = form.save(commit=False)
            rental_request.usb_device = usb_device
            rental_request.user = request.user
            rental_request.save()

            # デバイスをレンタル不可に変更
            usb_device.is_available = False
            usb_device.save()
            
            # メール送信とエラーハンドリング
            try:
                self.send_approval_email(rental_request)
            except SMTPException:
                # メール送信に失敗した場合のエラーメッセージ
                error_message = "レンタル申請が完了しましたが、承認者へのメール送信に失敗しました。"
                return render(request, 'rentals/request_rental_form.html', {'form': form, 'error_message': error_message})

            return redirect('usb_list')

        return render(request, 'rentals/request_rental_form.html', {'form': form, 'usb_device': usb_device})

    def send_approval_email(self, rental_request):
        """承認者にレンタル申請の通知メールを送信する"""
        subject = "USBレンタル申請の承認が必要です"
        message = (
            f"{rental_request.user.username}さんがUSBデバイス『{rental_request.usb_device.name}』の"
            "レンタルを申請しました。\n"
            f"承認者であるあなたの承認が必要です。\n"
            "レンタル開始日: {rental_request.start_date}\n"
            "返却期日: {rental_request.end_date}\n\n"
            "承認・却下を行ってください。"
        )
        recipient_list = [rental_request.approver.email]  # 承認者のメールアドレス
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    
class AddUserPCView(LoginRequiredMixin, CreateView):
    model = UserPC
    form_class = UserPCForm
    template_name = 'rentals/add_user_pc.html'
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        # 現在のユーザーをPCのユーザーに設定
        form.instance.user = self.request.user
        return super().form_valid(form)
    
class UserPCListView(LoginRequiredMixin, ListView):
    model = UserPC
    template_name = 'rentals/user_pc_list.html'
    context_object_name = 'user_pcs'

    def get_queryset(self):
        # ログインユーザーのPC情報のみを取得
        return UserPC.objects.filter(user=self.request.user)
    
class UserPCUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserPC
    form_class = UserPCForm
    template_name = 'rentals/user_pc_form.html'
    success_url = reverse_lazy('user_pc_list')

    def test_func(self):
        # ログインユーザーが所有するPCのみ編集可能
        user_pc = self.get_object()
        return user_pc.user == self.request.user
    
class UserPCDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = UserPC
    template_name = 'rentals/user_pc_confirm_delete.html'
    success_url = reverse_lazy('user_pc_list')

    def test_func(self):
        # ログインユーザーが所有するPCのみ削除可能
        user_pc = self.get_object()
        return user_pc.user == self.request.user


class ManufacturerWhitelistCreateView(LoginRequiredMixin, View):
    def get(self, request):
        manufacturer_form = ManufacturerForm()
        whitelist_form = ManufacturerWhitelistForm()
        return render(request, 'rentals/manufacturer_whitelist_form.html', {
            'manufacturer_form': manufacturer_form,
            'whitelist_form': whitelist_form,
        })

    def post(self, request):
        manufacturer_form = ManufacturerForm(request.POST)
        whitelist_form = ManufacturerWhitelistForm(request.POST)

        if manufacturer_form.is_valid():
            # 新しいメーカーを保存し、ホワイトリストにも追加
            manufacturer = manufacturer_form.save()
            ManufacturerWhitelist.objects.create(manufacturer=manufacturer)
            return redirect('whitelist_list')
        
        elif whitelist_form.is_valid():
            # 既存のメーカーをホワイトリストに追加
            whitelist_form.save()
            return redirect('whitelist_list')
        
        # エラーがあった場合は再度フォームを表示
        return render(request, 'rentals/manufacturer_whitelist_form.html', {
            'manufacturer_form': manufacturer_form,
            'whitelist_form': whitelist_form,
        })

class ManufacturerWhitelistListView(LoginRequiredMixin, ListView):
    model = ManufacturerWhitelist
    template_name = 'rentals/manufacturer_whitelist_list.html'
    context_object_name = 'whitelisted_manufacturers'

class ExtensionRequestView(LoginRequiredMixin, View):
    def get(self, request, rental_id):
        rental_request = get_object_or_404(RentalRequest, id=rental_id, user=request.user)
        form = ExtensionRequestForm(initial={'new_end_date': rental_request.end_date})
        return render(request, 'rentals/extension_request_form.html', {'form': form, 'rental_request': rental_request})

    def post(self, request, rental_id):
        rental_request = get_object_or_404(RentalRequest, id=rental_id, user=request.user)
        form = ExtensionRequestForm(request.POST)
        
        if form.is_valid():
            new_end_date = form.cleaned_data['new_end_date']
            rental_request.end_date = new_end_date  # 返却期日を更新
            rental_request.save()
            return redirect('usb_list')  # 一覧ページにリダイレクト
            
        return render(request, 'rentals/extension_request_form.html', {'form': form, 'rental_request': rental_request})
