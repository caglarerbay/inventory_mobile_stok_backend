# inventory/serializers.py

from rest_framework import serializers
from .models import (
    Product, UserStock, StockTransaction,
    ExternalProduct, Institution, DeviceType,
    DeviceRecord, Installation, Maintenance,
    Fault, InstitutionNote
)


from .models import DevicePartUsage

#
# Ürün / Stok / Transaction
#
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'part_code', 'name',
            'quantity', 'min_limit',
            'order_placed', 'cabinet', 'shelf',
        ]


class UserStockSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    cabinet = serializers.CharField(source='product.cabinet', read_only=True, allow_null=True)
    shelf   = serializers.CharField(source='product.shelf',   read_only=True, allow_null=True)

    class Meta:
        model = UserStock
        fields = [
            'id', 'user', 'product',
            'quantity', 'cabinet', 'shelf',
        ]


class StockTransactionSerializer(serializers.ModelSerializer):
    product     = ProductSerializer(read_only=True)
    user        = serializers.StringRelatedField()
    target_user = serializers.StringRelatedField()

    class Meta:
        model = StockTransaction
        fields = [
            'id', 'transaction_type', 'product',
            'quantity', 'user', 'target_user',
            'timestamp', 'description',
            'current_quantity',
            'current_user_quantity',
            'current_receiver_quantity',
        ]


class ExternalProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExternalProduct
        fields = ['part_code', 'name', 'devices', 'unit_price']


#
# Cihaz Tipleri
#
class DeviceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceType
        fields = ['id', 'name']


#
# Kurum listeleme (Flutter için)
#
class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ['id', 'name', 'city', 'contact_name', 'contact_phone']


#
# Kurulum kayıtları
#
class InstallationSerializer(serializers.ModelSerializer):
    institution            = serializers.CharField(source='institution.name', read_only=True)
    institution_id         = serializers.PrimaryKeyRelatedField(
                                queryset=Institution.objects.all(),
                                source='institution',
                            )
    device_id              = serializers.PrimaryKeyRelatedField(
                                queryset=DeviceRecord.objects.all(),
                                source='device',
                            )
    connected_core_id      = serializers.PrimaryKeyRelatedField(
                                queryset=DeviceRecord.objects.filter(device_type__is_core=True),
                                source='connected_core',
                                allow_null=True,
                                required=False
                            )
    device_serial          = serializers.CharField(source='device.serial_number', read_only=True)
    device_type            = serializers.CharField(source='device.device_type.name', read_only=True)
    connected_core_serial  = serializers.SerializerMethodField()

    class Meta:
        model = Installation
        fields = [
            'id',
            'device_id',
            'device_serial',
            'device_type',
            'connected_core_id',
            'connected_core_serial',
            'institution',
            'institution_id',
            'install_date',
            'uninstall_date',
        ]
        read_only_fields = [
            'id', 'device_serial', 'device_type',
            'connected_core_serial', 'institution',
        ]

    def get_connected_core_serial(self, obj):
        return obj.connected_core.serial_number if obj.connected_core else None


#
# Bakım kayıtları
#
class MaintenanceSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(source='device.serial_number', read_only=True)
    device_id     = serializers.PrimaryKeyRelatedField(queryset=DeviceRecord.objects.all(), source='device')

    class Meta:
        model = Maintenance
        fields = ['id', 'serial_number', 'device_id', 'date', 'personnel', 'notes']
        read_only_fields = ['id', 'serial_number']


#
# Arıza kayıtları
#
class FaultSerializer(serializers.ModelSerializer):
    serial_number = serializers.CharField(source='device.serial_number', read_only=True)
    device_id     = serializers.PrimaryKeyRelatedField(queryset=DeviceRecord.objects.all(), source='device')
    status        = serializers.SerializerMethodField()

    class Meta:
        model = Fault
        fields = [
            'id', 'serial_number', 'device_id',
            'fault_date', 'technician',
            'initial_notes', 'closing_notes',
            'closed_date', 'status',
        ]
        read_only_fields = ['id', 'serial_number', 'status']

    def get_status(self, obj):
        return 'open' if obj.closed_date is None else 'closed'


#
# Kurum notları
#
class InstitutionNoteSerializer(serializers.ModelSerializer):
    created_by     = serializers.StringRelatedField(source='user', read_only=True)
    note_date      = serializers.DateField(read_only=True)
    institution_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = InstitutionNote
        fields = ['id', 'institution_id', 'text', 'note_date', 'created_by']
        read_only_fields = ['id', 'note_date', 'created_by']

    def create(self, validated_data):
        inst_id = validated_data.pop('institution_id')
        user    = self.context['request'].user
        return InstitutionNote.objects.create(
            institution_id=inst_id,
            user=user,
            **validated_data
        )


#
# Cihaz Kayıt / Listeleme
#
class DeviceRecordSerializer(serializers.ModelSerializer):
    device_type           = serializers.CharField(source='device_type.name', read_only=True)
    institution           = serializers.CharField(source='institution.name', read_only=True)
    core_required         = serializers.BooleanField(source='device_type.core_required', read_only=True)
    device_type_id        = serializers.IntegerField(write_only=True, required=True)
    institution_id        = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    connected_core_serial = serializers.SerializerMethodField()

    class Meta:
        model = DeviceRecord
        fields = [
            'id',
            'serial_number',
            'device_type',
            'institution',
            'device_type_id',
            'institution_id',
            'core_required',
            'connected_core_serial',
        ]
        read_only_fields = ['id', 'device_type', 'institution', 'core_required']

    def get_connected_core_serial(self, obj):
        inst = obj.installations.filter(uninstall_date__isnull=True).order_by('-install_date').first()
        return inst.connected_core.serial_number if inst and inst.connected_core else None


#
# Cihaz Detay
#
class DeviceDetailSerializer(serializers.ModelSerializer):
    serial_number    = serializers.CharField(read_only=True)
    device_type      = serializers.CharField(source='device_type.name', read_only=True)
    core_required    = serializers.BooleanField(source='device_type.core_required', read_only=True)
    institution      = serializers.SerializerMethodField()
    connected_core   = serializers.SerializerMethodField()
    install_date     = serializers.SerializerMethodField()
    uninstall_date   = serializers.SerializerMethodField()
    installation_id  = serializers.SerializerMethodField()

    class Meta:
        model = DeviceRecord
        fields = [
            'id',
            'serial_number',
            'device_type',
            'institution',
            'core_required',
            'connected_core',
            'install_date',
            'uninstall_date',
            'installation_id',
        ]
        read_only_fields = fields

    def _get_active_install(self, obj):
        return Installation.objects.filter(
            device=obj,
            uninstall_date__isnull=True
        ).order_by('-install_date').first()

    def get_institution(self, obj):
        inst = self._get_active_install(obj)
        return inst.institution.name if inst else None

    def get_connected_core(self, obj):
        inst = self._get_active_install(obj)
        return inst.connected_core.serial_number if inst and inst.connected_core else None

    def get_install_date(self, obj):
        inst = self._get_active_install(obj)
        return inst.install_date if inst else None

    def get_uninstall_date(self, obj):
        inst = self._get_active_install(obj)
        return inst.uninstall_date if inst else None

    def get_installation_id(self, obj):
        inst = self._get_active_install(obj)
        return inst.id if inst else None




class DevicePartUsageSerializer(serializers.ModelSerializer):
    device_serial = serializers.CharField(source='device.serial_number', read_only=True)
    product_code = serializers.CharField(source='product.part_code', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    product_price = serializers.SerializerMethodField()  # ✅ fiyatı buradan çekiyoruz

    class Meta:
        model = DevicePartUsage
        fields = [
            'id', 'device', 'device_serial',
            'product', 'product_code', 'product_name',
            'quantity', 'user', 'user_username', 'used_at',
            'product_price'
        ]
        read_only_fields = [
            'used_at', 'device_serial', 'product_code',
            'product_name', 'user_username', 'product_price'
        ]

    def get_product_price(self, obj):
        code = obj.product.part_code if obj.product else None
        if not code:
            return None
        ext = ExternalProduct.objects.filter(part_code=code).first()
        return ext.unit_price if ext else None
