from django import forms
from .models import MenuItem, BahanBaku

class MenuForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['nama_menu', 'description', 'category', 'harga']

class BahanBakuForm(forms.ModelForm):
    class Meta:
        model = BahanBaku
        fields = ['name', 'stock', 'satuan']