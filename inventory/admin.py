# admin.py

# ——— Monkey-patch to drop unexpected 'single_object' kwarg ———
from django.contrib.admin.models import LogEntryManager

_original_log_action = LogEntryManager.log_action
def _patched_log_action(self,
                        user_id,
                        content_type_id,
                        object_id,
                        object_repr,
                        action_flag,
                        change_message,
                        *args, **kwargs):
    kwargs.pop('single_object', None)
    return _original_log_action(self,
                                user_id,
                                content_type_id,
                                object_id,
                                object_repr,
                                action_flag,
                                change_message)
LogEntryManager.log_action = _patched_log_action

_original_log_actions = getattr(LogEntryManager, 'log_actions', None)
if _original_log_actions:
    def _patched_log_actions(self, *args, **kwargs):
        kwargs.pop('single_object', None)
        return _original_log_actions(self, *args, **kwargs)
    LogEntryManager.log_actions = _patched_log_actions
# ————————————————————————————————————————————————————————————


from django import forms
from django.core.exceptions import ValidationError
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.formats import base_formats
from django.db import transaction
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import ExternalProduct

from .models import Product, UserStock, StockTransaction, DailyAccessCode, AppSettings




from import_export import fields, widgets


#cihaz ve kurum bilgileri importları
from .models import Institution, DeviceType, DeviceRecord, Installation, Maintenance, Fault, InstitutionNote

from .models import DevicePartUsage


User = get_user_model()

# Unregister/register User only once
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class UserStockInline(admin.TabularInline):
    model = UserStock
    extra = 0

class CustomUserAdmin(DefaultUserAdmin):
    inlines = [UserStockInline]

try:
    admin.site.register(User, CustomUserAdmin)
except admin.sites.AlreadyRegistered:
    pass


# Define a Resource for import/export
class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        # Use part_code as the lookup key
        import_id_fields = ('part_code',)
        fields = (
            'part_code',
            'name',
            'cabinet',
            'shelf',
            'quantity',
            'min_limit',
            'order_placed',
        )

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """
        After a successful import (not dry run), delete any Products
        whose part_code did not appear in the imported Excel.
        """
        if dry_run:
            return

        # Collect all part_codes from the uploaded dataset
        imported_codes = {
            row['part_code']
            for row in dataset.dict  # dataset.dict is a list of row‐dicts
        }

        # Delete any Product not present in imported_codes
        with transaction.atomic():
            Product.objects.exclude(part_code__in=imported_codes).delete()


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_class = ProductResource
    list_display = (
        'part_code', 'name', 'cabinet', 'shelf',
        'quantity', 'min_limit', 'order_placed',
    )
    search_fields = ('part_code', 'name')
    formats = (
        base_formats.XLSX,
        base_formats.CSV,
    )


@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp', 'transaction_type',
        'product', 'quantity', 'user', 'target_user'
    )
    list_filter = ('transaction_type', 'timestamp')


@admin.register(DailyAccessCode)
class DailyAccessCodeAdmin(admin.ModelAdmin):
    list_display = ('date', 'code')


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "critical_stock_email", "export_stock_email")


class ExternalProductResource(resources.ModelResource): #ppl için admin erişimi ve export import işlemleri
    class Meta:
        model = ExternalProduct
        import_id_fields = ('part_code',)
        fields = (
            'part_code',
            'name',
            'devices',
            'unit_price',
        )
        def import_data(self, dataset, dry_run=False, raise_errors=False,
                    use_transactions=None, collect_failed_rows=False, **kwargs):
            total_rows = getattr(dataset, 'total_rows', None) or dataset.height
            if total_rows <= 4000:
            # Küçük dosya: eski davranışla senkron import
                return super().import_data(
                dataset, dry_run=dry_run, raise_errors=raise_errors,
                use_transactions=use_transactions, collect_failed_rows=collect_failed_rows, **kwargs
            )
            # Büyük dosya: arkaplana bırakmak için exception ile bilgi vereceğiz
            raise Exception(
                f"ExternalProduct import büyük dosya (satır sayısı: {total_rows}). "
                "Lütfen API üzerinden upload edip task olarak çalıştırın."
        )


@admin.register(ExternalProduct)
class ExternalProductAdmin(ImportExportModelAdmin):
    resource_class = ExternalProductResource
    list_display = ('part_code', 'name', 'devices', 'unit_price')
    search_fields = ('part_code', 'name', 'devices')
    formats = (base_formats.XLSX, base_formats.CSV)


#cihaz bilgileri bölümü buradan başlıyor



# —— Institution ——
class InstitutionResource(resources.ModelResource):
    # Yalnızca bu alanlar export/import’ta görünsün, id olmasın
    class Meta:
        model = Institution
        import_id_fields = ('name',)
        fields = ('name','city','contact_name','contact_phone')

@admin.register(Institution)
class InstitutionAdmin(ImportExportModelAdmin):
    resource_class = InstitutionResource
    list_display  = ('name','city','contact_name','contact_phone')
    search_fields = ('name','city','contact_name')
    formats       = (base_formats.XLSX, base_formats.CSV)


# —— DeviceType ——
class DeviceTypeResource(resources.ModelResource):
    class Meta:
        model = DeviceType
        import_id_fields = ('name',)
        fields = ('name','category','core_required','is_core')

@admin.register(DeviceType)
class DeviceTypeAdmin(ImportExportModelAdmin):
    resource_class = DeviceTypeResource
    list_display  = ('name','category','core_required','is_core')
    list_filter   = ('core_required','is_core')
    search_fields = ('name','category')
    formats       = (base_formats.XLSX, base_formats.CSV)


# —— DeviceRecord ——
class DeviceRecordResource(resources.ModelResource):
    device_type = fields.Field(
        column_name='device_type',
        attribute='device_type',
        widget=widgets.ForeignKeyWidget(DeviceType, 'name')
    )

    institution = fields.Field(
        column_name='institution'
    )

    def dehydrate_institution(self, obj):
        inst = obj.installations.filter(uninstall_date__isnull=True).first()
        if inst:
            return inst.institution.name
        if obj.institution:
            return obj.institution.name
        return ''

    class Meta:
        model = DeviceRecord
        import_id_fields = ('serial_number',)
        fields = ('serial_number', 'device_type', 'institution')
        export_order = ('serial_number', 'device_type', 'institution')


@admin.register(DeviceRecord)
class DeviceRecordAdmin(ImportExportModelAdmin):
    resource_class = DeviceRecordResource
    list_display = (
        'serial_number',
        'device_type',
        'current_institution',
        'current_connected_core',
    )
    list_filter   = ('device_type',)
    search_fields = ('serial_number',)
    formats       = (base_formats.XLSX, base_formats.CSV)

    def current_institution(self, obj):
        inst = obj.installations.filter(uninstall_date__isnull=True).first()
        return inst.institution.name if inst else '—'
    current_institution.short_description = 'Kurum'

    def current_connected_core(self, obj):
        inst = obj.installations.filter(uninstall_date__isnull=True).first()
        return inst.connected_core.serial_number if inst and inst.connected_core else '—'
    current_connected_core.short_description = 'Bağlı Core'

#kurulum sökülüm kayıtlar

class InstallationForm(forms.ModelForm):
    class Meta:
        model = Installation
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        device = cleaned.get('device')
        connected = cleaned.get('connected_core')

        # CORE bağımlı cihaz için bağlı CORE zorunlu
        if device and device.device_type.core_required and not connected:
            raise ValidationError({
                'connected_core': 'Bu cihaz CORE bağımlı; bağlı bir CORE seçmelisiniz.'
            })
        return cleaned


# —————— Import/Export Resource ——————
class InstallationResource(resources.ModelResource):
    device = fields.Field(
        column_name='serial_number',
        attribute='device',
        widget=widgets.ForeignKeyWidget(DeviceRecord, 'serial_number')
    )
    institution = fields.Field(
        column_name='institution',
        attribute='institution',
        widget=widgets.ForeignKeyWidget(Institution, 'name')
    )
    install_date = fields.Field(column_name='install_date', attribute='install_date')
    uninstall_date = fields.Field(column_name='uninstall_date', attribute='uninstall_date')
    connected_core = fields.Field(
        column_name='connected_core_serial',
        attribute='connected_core',
        widget=widgets.ForeignKeyWidget(DeviceRecord, 'serial_number')
    )

    class Meta:
        model = Installation
        import_id_fields = ('device', 'install_date')
        fields = (
            'serial_number',
            'install_date',
            'uninstall_date',
            'institution',
            'connected_core_serial',
        )
        export_order = (
            'serial_number',
            'install_date',
            'uninstall_date',
            'institution',
            'connected_core_serial',
        )

    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        if dry_run:
            return

        from .models import Installation, DeviceRecord

        # Excel'den import edilen (device, install_date) kombinasyonlarını set olarak topla
        excel_keys = set()
        for row in dataset.dict:
            serial_number = row.get('serial_number')
            install_date = row.get('install_date')
            try:
                device = DeviceRecord.objects.get(serial_number=serial_number)
                if not install_date:
                    continue
                excel_keys.add((device.id, str(install_date)))
            except DeviceRecord.DoesNotExist:
                continue

        # Eğer excel_keys hiç oluşmamışsa, güvenlik için silme işlemi yapma!
        if not excel_keys:
            print("UYARI: Excel importunda hiç kayıt bulunamadı, silme işlemi yapılmadı.")
            return

        # DB'deki tüm (device, install_date) kombinasyonlarını bul (str ile!)
        db_keys = set(
            (device_id, str(install_date))
            for device_id, install_date in Installation.objects.values_list('device_id', 'install_date')
        )

        # Excel'de olmayan tüm DB kayıtlarını sil
        for device_id, install_date in db_keys - excel_keys:
            Installation.objects.filter(device_id=device_id, install_date=install_date).delete()






# —————— Admin Registration ——————
@admin.register(Installation)
class InstallationAdmin(ImportExportModelAdmin):
    form                = InstallationForm
    resource_class      = InstallationResource
    autocomplete_fields = ('device', 'institution', 'connected_core')
    list_display        = (
        'device_serial',
        'device_type',
        'institution',
        'connected_core_serial',
        'install_date',
        'uninstall_date',
    )
    list_filter         = ('install_date', 'uninstall_date', 'institution')
    search_fields       = ('device__serial_number', 'institution__name')
    formats             = (base_formats.XLSX, base_formats.CSV)

    def device_serial(self, obj):
        return obj.device.serial_number
    device_serial.short_description = 'Seri No'

    def device_type(self, obj):
        return obj.device.device_type.name
    device_type.short_description = 'Cihaz Tipi'

    def connected_core_serial(self, obj):
        return obj.connected_core.serial_number if obj.connected_core else '—'
    connected_core_serial.short_description = 'Bağlı Core'

    def get_readonly_fields(self, request, obj=None):
        if obj:
            # Change form: yalnızca söküm tarihi düzenlenebilir
            return ('device', 'institution', 'install_date', 'connected_core')
        return ()

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Add form: tüm cihazlar / core’lar listelensin
        # Change form: kilitlediğimiz alanlar zaten readonly_fields’da
        if db_field.name == 'device':
            active_ids = Installation.objects.filter(
                uninstall_date__isnull=True
            ).values_list('device_id', flat=True)
            qs = DeviceRecord.objects.exclude(id__in=active_ids)

            object_id = request.resolver_match.kwargs.get('object_id')
            if object_id:
                try:
                    inst = Installation.objects.get(pk=object_id)
                    qs = qs | DeviceRecord.objects.filter(pk=inst.device_id)
                except Installation.DoesNotExist:
                    pass

            kwargs['queryset'] = qs

        if db_field.name == 'connected_core':
            qs = DeviceRecord.objects.filter(
                device_type__is_core=True,
                installations__uninstall_date__isnull=True
            )
            institution_id = request.POST.get('institution') or request.GET.get('institution')
            if institution_id:
                qs = qs.filter(installations__institution_id=institution_id)
            kwargs['queryset'] = qs

        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
#bakım kayıtları buradan başlıyor

class MaintenanceResource(resources.ModelResource):
    device = fields.Field(
        column_name='serial_number',
        attribute='device',
        widget=widgets.ForeignKeyWidget(DeviceRecord, 'serial_number')
    )
    date = fields.Field(column_name='date',       attribute='date')
    personnel = fields.Field(column_name='personnel', attribute='personnel')
    notes = fields.Field(column_name='notes',     attribute='notes')

    class Meta:
        model = Maintenance
        import_id_fields = ('device', 'date')
        fields = ('serial_number', 'date', 'personnel', 'notes')
        export_order = ('serial_number', 'date', 'personnel', 'notes')

@admin.register(Maintenance)
class MaintenanceAdmin(ImportExportModelAdmin):
    resource_class = MaintenanceResource
    list_display   = ('device_serial', 'date', 'personnel')
    list_filter    = ('date', 'device__device_type')
    search_fields  = ('device__serial_number', 'personnel')
    formats        = (base_formats.XLSX, base_formats.CSV)

    def device_serial(self, obj):
        return obj.device.serial_number
    device_serial.short_description = 'Seri No'

#arıza kayıtları buradan başlıyor

class FaultResource(resources.ModelResource):
    device = fields.Field(
        column_name='serial_number',
        attribute='device',
        widget=widgets.ForeignKeyWidget(DeviceRecord, 'serial_number')
    )
    fault_date    = fields.Field(column_name='fault_date',   attribute='fault_date')
    technician    = fields.Field(column_name='technician',   attribute='technician')
    initial_notes = fields.Field(column_name='initial_notes', attribute='initial_notes')
    closing_notes = fields.Field(column_name='closing_notes', attribute='closing_notes')
    closed_date   = fields.Field(column_name='closed_date',  attribute='closed_date')

    class Meta:
        model = Fault
        import_id_fields = ('device', 'fault_date')
        fields = (
            'serial_number',
            'fault_date',
            'technician',
            'initial_notes',
            'closing_notes',
            'closed_date'
        )
        export_order = fields

@admin.register(Fault)
class FaultAdmin(ImportExportModelAdmin):
    resource_class = FaultResource
    list_display   = (
        'device_serial',
        'fault_date',
        'technician',
        'status_display',   # <-- değişiklik burada
        'closed_date'
    )
    list_filter    = ('fault_date', 'closed_date')
    search_fields  = ('device__serial_number', 'technician')
    formats        = (base_formats.XLSX, base_formats.CSV)

    def device_serial(self, obj):
        return obj.device.serial_number
    device_serial.short_description = 'Seri No'

    def status_display(self, obj):
        # obj.status() modelde tanımlıysa onu kullanabiliriz
        return obj.status()
    status_display.short_description = 'Durum'


#kurum npt bilgisi giriş kayıtları buradan başlıyor

class InstitutionNoteResource(resources.ModelResource):
    institution = fields.Field(
        column_name='institution',
        attribute='institution',
        widget=widgets.ForeignKeyWidget(Institution, 'name')
    )
    note_date   = fields.Field(column_name='note_date', attribute='note_date')
    text        = fields.Field(column_name='text',      attribute='text')

    class Meta:
        model = InstitutionNote
        import_id_fields = ('institution', 'note_date')
        fields = ('institution', 'note_date', 'text')
        export_order = ('institution', 'note_date', 'text')

@admin.register(InstitutionNote)
class InstitutionNoteAdmin(ImportExportModelAdmin):
    resource_class = InstitutionNoteResource
    list_display   = ('institution', 'note_date', 'short_text')
    list_filter    = ('note_date', 'institution')
    search_fields  = ('institution__name', 'text')
    formats        = (base_formats.XLSX, base_formats.CSV)

    def short_text(self, obj):
        # Uzun notları kısaltarak göster
        return (obj.text[:75] + '…') if len(obj.text) > 75 else obj.text
    short_text.short_description = 'Not Özeti'



@admin.register(DevicePartUsage)
class DevicePartUsageAdmin(admin.ModelAdmin):
    list_display = ('device', 'product', 'quantity', 'user', 'used_at')
    search_fields = ('device__serial_number', 'product__part_code', 'user__username')
    list_filter = ('used_at',)