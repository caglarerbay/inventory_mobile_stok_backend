from django.urls import path
from rest_framework.authtoken import views as drf_auth_views
from django.http import HttpResponse
from django.contrib import admin

from .views import (
    # Auth & user
    register_user, login_user, forgot_password_user,
    # Stock endpoints
    search_product, my_stock, use_product_api, transfer_product_api,
    admin_add_product, admin_update_stock,
    user_list, take_product, return_product,
    admin_adjust_user_stock, admin_list_user_stocks,
    transaction_log_api, critical_stock_api,
    send_excel_report_email_api, export_all_products_excel, import_products_excel,send_full_stock_report_api, toggle_order_placed,
    # App settings
    admin_update_min_limit, admin_update_app_settings, admin_get_app_settings, admin_generate_daily_code,
    direct_transfer_product,
    # Notifications
    send_push_notification, save_device_token, notification_history, delete_notification,
    ExternalProductList,
    # Maintenance & Faults
    MaintenanceListCreateAPIView,
    FaultListCreateAPIView, FaultRetrieveUpdateAPIView,
    # Institution & Notes
    InstitutionRetrieveUpdateAPIView,
    InstitutionListCreateAPIView,
    InstitutionNoteListCreateAPIView, InstitutionNoteRetrieveUpdateDestroyAPIView,
    # Device types & records
    DeviceTypeListAPIView,
    DeviceRecordListCreateAPIView, DeviceDetailAPIView,
    # Installation (kaldırılan InstallationListByDeviceAPIView yok)
    InstallationListByInstitutionAPIView,
    InstallationListCreateAPIView,
    InstallationRetrieveUpdateAPIView,
    DeviceRecordListCreateAPIView,
    DeviceRecordDetailAPIView
)

def home(request):
    return HttpResponse("Hoş geldiniz, Django backend çalışıyor!")

urlpatterns = [
    # Root
    path('', home, name='home'),

    # Auth / user management
    path('api/register/', register_user, name='register_user'),
    path('api/login/', login_user, name='login_user'),
    path('api/forgot_password/', forgot_password_user, name='forgot_password_user'),
    path('api-token-auth/', drf_auth_views.obtain_auth_token),

    # Product / stock endpoints
    path('api/search_product/', search_product, name='search_product'),
    path('api/my_stock/', my_stock, name='my_stock'),
    path('api/use_product/<int:product_id>/', use_product_api, name='use_product_api'),
    path('api/transfer_product/<int:product_id>/', transfer_product_api, name='transfer_product_api'),
    path('api/admin_add_product/', admin_add_product, name='admin_add_product'),
    path('api/admin_update_stock/<int:product_id>/', admin_update_stock, name='admin_update_stock'),
    path('api/take_product/<int:product_id>/', take_product, name='take_product'),
    path('api/direct_transfer_product/<int:product_id>/', direct_transfer_product, name='direct_transfer_product'),
    path('api/return_product/<int:product_id>/',return_product,name='return_product'),

    # User-stock management
    path('api/user_list/', user_list, name='user_list'),
    path('api/admin_list_user_stocks/', admin_list_user_stocks, name='admin_list_user_stocks'),
    path('api/admin_adjust_user_stock/', admin_adjust_user_stock, name='admin_adjust_user_stock'),
    path('api/transaction_log_api/', transaction_log_api, name='transaction_log_api'),
    path('api/critical_stock_api/', critical_stock_api, name='critical_stock_api'),
    path(
        'api/critical_stock_api/<int:product_id>/toggle_order/',
        toggle_order_placed,
        name='critical_stock_toggle'
    ),

    # Excel export/import
    path('api/send_excel_report_email_api/', send_excel_report_email_api, name='send_excel_report_email_api'),
    path('api/send_full_stock_report/', send_full_stock_report_api, name='send_full_stock_report_api'),
    path('api/export_all_products_excel/', export_all_products_excel, name='export_all_products_excel'),
    path('api/import_products_excel/', import_products_excel, name='import_products_excel'),

    # App settings
    path('api/admin_update_min_limit/<int:product_id>/', admin_update_min_limit, name='admin_update_min_limit'),
    path('api/admin_update_app_settings/', admin_update_app_settings, name='admin_update_app_settings'),
    path('api/admin_get_app_settings/', admin_get_app_settings, name='admin_get_app_settings'),
    path('api/admin_generate_daily_code/', admin_generate_daily_code, name='admin_generate_daily_code'),
    path('api/direct_transfer_product/', direct_transfer_product, name='direct_transfer_product'),

    # Push notifications
    path('api/send_push_notification/', send_push_notification, name='send_push_notification'),
    path('api/save_device_token/', save_device_token, name='save_device_token'),
    path('api/notification_history/', notification_history, name='notification_history'),
    path('api/delete_notification/<int:notif_id>/', delete_notification, name='delete_notification'),

    # External products for PPL
    path('api/external-products/', ExternalProductList.as_view(), name='external_products'),

    # Maintenance
    path('api/maintenance/', MaintenanceListCreateAPIView.as_view(), name='maintenance-list-create'),

    # Faults
    path('api/faults/', FaultListCreateAPIView.as_view(), name='faults-list-create'),
    path('api/faults/<int:pk>/', FaultRetrieveUpdateAPIView.as_view(), name='fault-detail'),

    # Institution & Notes
    path('api/institutions/<int:pk>/', InstitutionRetrieveUpdateAPIView.as_view(), name='institution-detail'),
    path('api/institutions/', InstitutionListCreateAPIView.as_view(), name='institution-list-create'),
    path('api/institution-notes/', InstitutionNoteListCreateAPIView.as_view(), name='institution-notes-list-create'),
    path('api/institution-notes/<int:pk>/', InstitutionNoteRetrieveUpdateDestroyAPIView.as_view(), name='institution-note-detail'),

    # Device types & records
    path('api/device-types/', DeviceTypeListAPIView.as_view(), name='device-types-list'),
    path('api/device-records/', DeviceRecordListCreateAPIView.as_view(), name='device-records-list-create'),
    path('api/device-records/<int:pk>/', DeviceDetailAPIView.as_view(), name='device-detail'),

    # Installation endpoints
    #   • Kuruma göre tüm kurulum/söküm geçmişi
    path(
        'api/institutions/<int:pk>/installations/',
        InstallationListByInstitutionAPIView.as_view(),
        name='institution-installations'
    ),
    #   • Tek bir kurulum kaydı GET/PATCH
    path(
        'api/installations/<int:pk>/',
        InstallationRetrieveUpdateAPIView.as_view(),
        name='installation-detail'
    ),
    #   • Cihaza göre listeleme ve yeni kayıt (GET?device_id=X, POST)
    path(
        'api/installations/',
        InstallationListCreateAPIView.as_view(),
        name='installation-list-create'
    ),

    #cihaz core bağlantısı bilgisi
    path('api/device-records/', DeviceRecordListCreateAPIView.as_view(), name='device-records'),
    path('api/device-records/<int:pk>/', DeviceRecordDetailAPIView.as_view(), name='device-record-detail'),

]
