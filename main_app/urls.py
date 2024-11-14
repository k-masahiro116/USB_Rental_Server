from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),  # ホームページ
    path('signup/', views.SignupView.as_view(), name='signup'),  # サインアップ
    path('device/add/', views.USBDeviceCreateView.as_view(), name='usb_device_create'),  # USBデバイス登録
    path('device/<int:pk>/', views.USBDeviceDetailView.as_view(), name='usb_device_detail'),  # USBデバイス詳細
    path('device/<int:pk>/edit/', views.USBDeviceUpdateView.as_view(), name='usb_device_edit'),  # USBデバイス編集
    path('device/<int:pk>/delete/', views.USBDeviceDeleteView.as_view(), name='usb_device_delete'),  # USBデバイス削除
    path('rentals/', views.USBListView.as_view(), name='usb_list'),  # USBリスト閲覧
    path('rentals/request/<int:usb_id>/', views.RequestRentalView.as_view(), name='request_rental'),  # レンタル申請
    path('rentals/return/<int:usb_id>/', views.ReturnUSBView.as_view(), name='return_usb'),  # 返却申請フォーム
    path('rentals/extension/<int:rental_id>/', views.ExtensionRequestView.as_view(), name='extension_request'),  # 延長申請
    path('pc/add/', views.AddUserPCView.as_view(), name='add_user_pc'),  # 利用PC追加
    path('pc/list/', views.UserPCListView.as_view(), name='user_pc_list'),  # 利用PC一覧
    path('pc/edit/<int:pk>/', views.UserPCUpdateView.as_view(), name='user_pc_edit'),  # 利用PC編集
    path('pc/delete/<int:pk>/', views.UserPCDeleteView.as_view(), name='user_pc_delete'),  # 利用PC削除
    path('whitelist/add/', views.ManufacturerWhitelistCreateView.as_view(), name='whitelist_add'),  # ホワイトリスト登録
    path('whitelist/', views.ManufacturerWhitelistListView.as_view(), name='whitelist_list'),  # ホワイトリスト一覧
]
