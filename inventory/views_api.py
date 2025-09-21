# inventory/views_api.py
from rest_framework import generics, permissions
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

import tempfile
import os
import uuid
import io
import sys
import openpyxl


from .models import Product, UserStock, StockTransaction
from .serializers import (
    ProductSerializer,
    UserStockSerializer,
    StockTransactionSerializer,
    ExternalProductSerializer
)
from . import external_importer
from .external_importer import run_import_institutions
from .external_importer import run_products_import
from .external_importer import run_import_installations
from .external_importer import run_device_records_import



from rest_framework import viewsets, permissions, filters
from .models import DevicePartUsage
from .serializers import DevicePartUsageSerializer
from rest_framework import viewsets, permissions, filters, serializers
from .models import DevicePartUsage, UserStock, StockTransaction








# Ürünleri listeleyen view
class ProductListAPIView(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

# Yeni ürün ekleme için (POST işlemi)
class ProductCreateAPIView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

# Kullanıcının kendi stoklarını listeleyen view
class UserStockListAPIView(generics.ListAPIView):
    serializer_class = UserStockSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserStock.objects.filter(user=self.request.user)

# Stock transaction’ları listeleyen view
class StockTransactionListAPIView(generics.ListAPIView):
    queryset = StockTransaction.objects.all().order_by('-timestamp')
    serializer_class = StockTransactionSerializer
    permission_classes = [IsAdminUser]


# Büyük Excel’i arka planda parçalayacak endpoint
@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_external_products_excel(request):
    excel_file = request.FILES.get('file')
    if not excel_file:
        return Response({"detail": "file alanı eksik."}, status=400)

    # Geçici klasöre kaydet
    tmp_dir = os.path.join(tempfile.gettempdir(), 'temp_imports')
    os.makedirs(tmp_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{excel_file.name}"
    file_path = os.path.join(tmp_dir, unique_name)
    with open(file_path, 'wb+') as f:
        for chunk in excel_file.chunks():
            f.write(chunk)

    # SENKRON İÇE AKTARMAYI ÇAĞIR
    try:
        external_importer.run_import(file_path)
    except Exception as e:
        return Response({"detail": f"Import hatası: {str(e)}"}, status=500)

    return Response({"detail": "ExternalProduct import başarıyla tamamlandı."}, status=200)

#kurumlar için api üzerinden import excel
@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_institutions_excel(request):
    excel_file = request.FILES.get('file')
    if not excel_file:
        return Response({"detail": "file alanı eksik."}, status=400)

    # Geçici klasöre kaydet
    tmp_dir = os.path.join(tempfile.gettempdir(), 'temp_imports')
    os.makedirs(tmp_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{excel_file.name}"
    file_path = os.path.join(tmp_dir, unique_name)
    with open(file_path, 'wb+') as f:
        for chunk in excel_file.chunks():
            f.write(chunk)

    # Senkron import’u çağır
    try:
        run_import_institutions(file_path)
    except Exception as e:
        return Response({"detail": f"Import hatası: {str(e)}"}, status=500)

    return Response({"detail": "Institution import başarıyla tamamlandı."}, status=200)

#ürünler için api üzerinden import excel
@api_view(['POST'])
@permission_classes([IsAdminUser])
def import_products_excel_batch(request):
    excel_file = request.FILES.get('file')
    if not excel_file:
        return Response({"detail": "file alanı eksik."}, status=400)

    tmp_dir = os.path.join(tempfile.gettempdir(), 'temp_imports')
    os.makedirs(tmp_dir, exist_ok=True)
    unique = f"{uuid.uuid4().hex}_{excel_file.name}"
    file_path = os.path.join(tmp_dir, unique)
    with open(file_path, 'wb+') as f:
        for chunk in excel_file.chunks():
            f.write(chunk)

    try:
        excel_codes, db_codes, deleted_count = run_products_import(file_path)
    except Exception as e:
        return Response({"detail": f"Import hatası: {str(e)}"}, status=500)

    return Response({
        "detail": "Batch import tamamlandı.",
        "excel_codes": excel_codes,
        "db_codes": db_codes,
        "deleted_count": deleted_count,
    }, status=200)


#cihazlar için api üzerinden import excel
@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def import_device_records_excel(request):
    excel_file = request.FILES.get('file')
    if not excel_file:
        return Response({"detail": "file alanı eksik."}, status=400)

    # Geçici klasöre kaydet
    tmp_dir = os.path.join(tempfile.gettempdir(), 'temp_imports')
    os.makedirs(tmp_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}_{excel_file.name}"
    file_path = os.path.join(tmp_dir, unique_name)
    with open(file_path, 'wb+') as f:
        for chunk in excel_file.chunks():
            f.write(chunk)

    # SENKRON İÇE AKTAR
    try:
        run_device_records_import(file_path)
    except Exception as e:
        return Response({"detail": f"Import hatası: {str(e)}"}, status=500)

    return Response({"detail": "DeviceRecord import başarıyla tamamlandı."}, status=200)

#kurulumlar için api üzerinden import excel
@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def import_installations_excel(request):
    # 1) Dosya var mı?
    excel_file = request.FILES.get('file')
    if not excel_file:
        return Response({"detail": "file alanı eksik."}, status=400)

    # 2) Geçici klasöre kaydet
    tmp_dir = os.path.join(tempfile.gettempdir(), 'temp_imports')
    os.makedirs(tmp_dir, exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}_{excel_file.name}"
    file_path = os.path.join(tmp_dir, unique_name)
    with open(file_path, 'wb+') as f:
        for chunk in excel_file.chunks():
            f.write(chunk)

    # 3) Import’u çalıştır
    try:
        run_import_installations(file_path)
    except Exception as e:
        return Response({"detail": f"Import hatası: {e}"}, status=500)

    # 4) Başarılı yanıt
    return Response(
        {"detail": "Installation import başarıyla tamamlandı."},
        status=200
    )





class DevicePartUsageViewSet(viewsets.ModelViewSet):
    serializer_class = DevicePartUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['device__serial_number', 'product__part_code']

    def get_queryset(self):
        queryset = DevicePartUsage.objects.all().order_by('-used_at')
        device_id = self.request.query_params.get('device')
        if device_id:
            return queryset.filter(device_id=device_id)
        return queryset.none()

    def perform_create(self, serializer):
        usage = serializer.save(user=self.request.user)
        user = self.request.user
        product = usage.product
        quantity = usage.quantity

        user_stock = UserStock.objects.filter(user=user, product=product).first()
        if not user_stock or user_stock.quantity < quantity:
            raise serializers.ValidationError('Kişisel stokta yeterli ürün yok!')

        user_stock.quantity -= quantity
        current_qty_for_log = user_stock.quantity
        user_stock.save()
        if user_stock.quantity == 0:
            user_stock.delete()
            current_qty_for_log = 0

        StockTransaction.objects.create(
            product=product,
            transaction_type="USE",
            quantity=quantity,
            user=user,
            description=f"Cihazda parça kullanımı: {usage.device.serial_number}",
            current_user_quantity=current_qty_for_log
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stock_movements_api(request):
    """
    GET /api/stock-movements/
    Yalnızca 'TAKE' ve 'RETURN' tipindeki StockTransaction kayıtlarını
    döner. Tüm oturum açmış kullanıcılar görebilir.
    """
    queryset = StockTransaction.objects.filter(
        transaction_type__in=['TAKE', 'RETURN']
    ).order_by('-timestamp')
    serializer = StockTransactionSerializer(queryset, many=True)
    return Response({"transactions": serializer.data}, status=200)