from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import models
from django.contrib.auth import get_user_model
# Ürün modelimiz: ana stokta yer alan parçalar.

class Product(models.Model):
    part_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    cabinet = models.CharField(max_length=5, blank=True, null=True)
    shelf   = models.CharField(max_length=5, blank=True, null=True)
    quantity = models.PositiveIntegerField(default=0)
    # Varsayılan olarak 0, yani quantity <= 0 olursa kritik stok.
    min_limit = models.PositiveIntegerField(
        default=0,
        help_text="Bu değer 0 ise ürün adedi 0 olduğunda kritik stok sayılır. "
                  "Eğer 5 gibi bir değer girilirse ürün adedi 5 veya altına düştüğünde kritik stok sayılır."
    )
    
    order_placed = models.BooleanField(
        default=False, 
        help_text="Bu ürün için sipariş çekildiyse True olur."
    )


    def __str__(self):
        return f"{self.part_code} - {self.name}"





# Kullanıcı stoklarını tutan model
class UserStock(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="stocks")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="user_stocks")
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} - {self.product.part_code} : {self.quantity}"


# Stok hareketlerinin loglanması için model
class StockTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('IN', 'Ana Stok Girişi'),
        ('UPDATE', 'Ana Stok Güncelleme'),
        ('TAKE', 'Kullanıcının Ana Stoktan Alması'),
        ('RETURN', 'Kullanıcının Ana Stoka İade Etmesi'),
        ('TRANSFER', 'Kullanıcılar Arası Transfer'),
        ('USE', 'Kullanım'),
        ('ADJUST', 'Admin Stok Ayarı'),
        ('O_TRANSFER', 'Diğer Transfer'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="transactions")
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="received_transactions")
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True, null=True)
    # Ana stok için güncel miktar:
    current_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="İşlem sonrası ana stok miktarı")
    # İşlem yapan kullanıcının stoğunda kalan miktar (örneğin TAKE, RETURN, USE işlemlerinde):
    current_user_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="İşlem sonrası kullanıcının stoğundaki miktar")
    # Transfer işleminde, alıcı kullanıcının stoğundaki güncel miktar:
    current_receiver_quantity = models.PositiveIntegerField(null=True, blank=True, help_text="Transfer işleminde alıcının stoğundaki miktar")

    def __str__(self):
        return f"{self.transaction_type} - {self.product.part_code} - {self.quantity}"



# Günlük 10 haneli kodu tutan model (bu kod admin tarafından güncellenip her gün değişecek)
class DailyAccessCode(models.Model):
    code = models.CharField(max_length=10)
    date = models.DateField(unique=True)

    def __str__(self):
        return f"{self.date} - {self.code}"

#telefona gidecek olan bildirimler
class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_token}"


# models.py



class AppSettings(models.Model):
    # Kritik stok raporunun gideceği adres
    critical_stock_email = models.EmailField(
        default="kritik@example.com",
        help_text="Kritik stok raporu bu mail adresine gönderilecek."
    )
    # Dışa aktar (tüm stok) raporunun gideceği adres
    export_stock_email = models.EmailField(
        default="export@example.com",
        help_text="Tüm stok raporu bu mail adresine gönderilecek."
    )

    def __str__(self):
        return "Uygulama Ayarları"


class NotificationLog(models.Model):
    title = models.CharField(max_length=255)
    message = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.sent_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.title}"
    

class ExternalProduct(models.Model): #ppl için hazırlanan model
    part_code  = models.CharField(max_length=50, unique=True)
    name       = models.CharField(max_length=200)
    devices    = models.CharField(
        max_length=500,
        help_text="Bu ürünün kullanıldığı cihazlar (virgülle ayrılmış)."
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.part_code} – {self.name}"
    
#cihaz bilgileri için modeller/////////////////////////////

class Institution(models.Model):
    name           = models.CharField("Kurum Adı", max_length=255)
    city           = models.CharField("Şehir",   max_length=100)
    contact_name   = models.CharField("İrtibat Kişisi", max_length=200)
    contact_phone  = models.CharField("Telefon",       max_length=20)

    def __str__(self):
        return f"{self.name} ({self.city})"


class DeviceType(models.Model):
    name           = models.CharField("Cihaz Adı",      max_length=100, unique=True)
    category       = models.CharField("Tip",            max_length=100)
    core_required  = models.BooleanField("Core Bağımlılığı", default=False)
    is_core        = models.BooleanField("CORE",           default=False)

    def __str__(self):
        return f"{self.name} – {self.category}"


class DeviceRecord(models.Model):
    device_type   = models.ForeignKey(DeviceType, on_delete=models.CASCADE)
    serial_number = models.CharField(max_length=100, unique=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    institution   = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='device_records'
    )

    def __str__(self):
        # Cihaz tipi ve seri numarasını birleştiriyoruz
        return f"{self.device_type.name} – {self.serial_number}"
    

    #kurulum sökülüm sayfası modeli

class Installation(models.Model):
    device         = models.ForeignKey(
        'DeviceRecord', on_delete=models.CASCADE,
        related_name='installations', verbose_name='Cihaz'
    )
    institution    = models.ForeignKey(
        'Institution', on_delete=models.CASCADE,
        related_name='installations', verbose_name='Kurum'
    )
    install_date   = models.DateField('Kurulum Tarihi')
    uninstall_date = models.DateField(
        'Söküm Tarihi', null=True, blank=True,
        help_text='Boşsa hâlen kurulu'
    )
    # <<< Yeni alan:
    connected_core = models.ForeignKey(
        'DeviceRecord',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'device_type__is_core': True},
        related_name='child_installations',
        verbose_name='Bağlı Core'
    )

    def __str__(self):
        base = f"{self.device.serial_number} @ {self.institution.name}"
        if self.connected_core:
            base += f" → Core: {self.connected_core.serial_number}"
        return base
    
#bakımlar bu alanda tutulacak

class Maintenance(models.Model):
    device    = models.ForeignKey(
        'DeviceRecord',
        on_delete=models.CASCADE,
        related_name='maintenances',
        verbose_name='Cihaz'
    )
    date      = models.DateField('Bakım Tarihi')
    personnel = models.CharField(
        'Bakımı Yapanlar',
        max_length=255,
        help_text='İsimleri virgülle ayırarak girin'
    )
    notes     = models.TextField('Notlar', blank=True)

    def __str__(self):
        return f"{self.date} – {self.device.serial_number}"
    
#cihaz arıza bilgileri için model

class Fault(models.Model):
    device      = models.ForeignKey(
        'DeviceRecord',
        on_delete=models.CASCADE,
        related_name='faults',
        verbose_name='Cihaz'
    )
    fault_date  = models.DateField('Müdahale Tarihi')
    technician  = models.CharField(
        'Müdahale Eden',
        max_length=255,
        help_text='İsimleri virgülle ayırarak girin'
    )
    # Başlangıç notu: müdahalede neler yapıldı, parça sipariş edildi vs.
    initial_notes = models.TextField(
        'Müdahale Notları',
        blank=True,
        help_text='İlk müdahalede alınan notlar'
    )
    # Kapanış notu: arıza kapatılırken yapılan işlemler
    closing_notes = models.TextField(
        'Kapanış Notları',
        blank=True,
        help_text='Arıza kapatılırken eklenen notlar'
    )
    closed_date = models.DateField(
        'Kapatılma Tarihi',
        null=True, blank=True,
        help_text='Boşsa açık (open), doluysa kapalı (closed)'
    )

    def __str__(self):
        return f"{self.fault_date} – {self.device.serial_number}"
    def status(self):
        return 'Open' if self.closed_date is None else 'Closed'
    
#kurum ile ilgili notlar bölümü

User = get_user_model()

class InstitutionNote(models.Model):
    institution = models.ForeignKey(
        'Institution',
        on_delete=models.CASCADE,
        related_name='notes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='institution_notes',
        null=True,
        blank=True
    )
    note_date = models.DateField(
        'Not Tarihi',
        help_text='Notun alındığı tarih',
        auto_now_add=True
    )
    text = models.TextField(
        'Not Metni',
        help_text='Kurumla ilgili serbest metin'
    )

    def __str__(self):
        return f"{self.institution.name} – {self.note_date:%Y-%m-%d}"
    




class DevicePartUsage(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='device_usages')
    device = models.ForeignKey('DeviceRecord', on_delete=models.CASCADE, related_name='used_parts')
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Kullanılan Parça"
        verbose_name_plural = "Kullanılan Parçalar"
        ordering = ['-used_at']

    def __str__(self):
        return f"{self.device.serial_number} için {self.product.part_code} ({self.quantity} adet)"
