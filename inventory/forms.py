from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Product

class CustomUserCreationForm(UserCreationForm):
    access_code = forms.CharField(
        max_length=10,
        help_text="Admin tarafından verilen 10 haneli kodu giriniz."
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'access_code', 'password1', 'password2')

class ProductForm(forms.ModelForm):
        class Meta:
            model = Product
            fields = ['part_code', 'name', 'quantity']

class ProductAddForm(forms.Form):
    part_code = forms.CharField(max_length=50, label="Parça Kodu")
    name = forms.CharField(max_length=200, label="Parça İsmi")
    quantity = forms.IntegerField(min_value=1, label="Adet")

class TakeProductForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1, label="Alınacak Miktar")



class ReturnProductForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1, label="İade Edilecek Miktar")

class TransferProductForm(forms.Form):
    # Alıcı kullanıcıyı girebilmek için basitçe username kullanalım.
    target_username = forms.CharField(max_length=150, label="Alıcı Kullanıcı Adı")
    quantity = forms.IntegerField(min_value=1, label="Transfer Edilecek Miktar")


class UseProductForm(forms.Form):
    product_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1, label="Kullanılacak Miktar")


class PushNotificationForm(forms.Form):
    title = forms.CharField(max_length=255, label="Bildirim Başlığı")
    message = forms.CharField(widget=forms.Textarea, label="Bildirim Mesajı")
