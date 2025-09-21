from django.urls import path
from .views_api import (
    ProductListAPIView,
    ProductCreateAPIView,
    UserStockListAPIView,
    StockTransactionListAPIView,
)
from .views_api import import_external_products_excel
from .views_api import import_institutions_excel
from .views_api import import_products_excel_batch
from .views_api import import_device_records_excel
from .views_api import import_installations_excel

from .views_api import DevicePartUsageViewSet
from .views_api import stock_movements_api

urlpatterns = [
    path('products/', ProductListAPIView.as_view(), name='api-product-list'),
    path('products/create/', ProductCreateAPIView.as_view(), name='api-product-create'),
    path('user-stocks/', UserStockListAPIView.as_view(), name='api-user-stocks'),
    path('transactions/', StockTransactionListAPIView.as_view(), name='api-transactions'),
    path('import_external_products_excel/', import_external_products_excel, name='import_external_products_excel'),
    path('import_institutions_excel/', import_institutions_excel, name='import_institutions_excel'),
    path('import_products_excel/batch/', import_products_excel_batch, name='import_products_excel_batch'),
    path('import_device_records_excel/', import_device_records_excel, name='import_device_records_excel'),
    path('import_installations_excel/', import_installations_excel, name='import_installations_excel'),


    path('device-part-usage/', DevicePartUsageViewSet.as_view({'get': 'list', 'post': 'create'}), name='device-part-usage-list-create'),
    path('device-part-usage/<int:pk>/', DevicePartUsageViewSet.as_view({'get': 'retrieve'}), name='device-part-usage-detail'),
    path('stock-movements/', stock_movements_api, name='api-stock-movements'),
]
