from django.db import models


class BahanBaku(models.Model):
    name = models.CharField(max_length=255)
    stock = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    satuan = models.CharField(max_length=255)

class MenuItem(models.Model):
    nama_menu = models.CharField(max_length=255)
    description = models.TextField()
    harga = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    category = models.CharField(choices=[('beverages', 'Beverages'), ('dishes', 'Dishes'), ('dessert', 'Dessert')], max_length=10, null=True)
    bahan_baku = models.ManyToManyField(BahanBaku, null=True)
    gambar = models.ImageField(upload_to='menu_images/', null=True, blank=True)

class BahanBakuPerMenu(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, null=True)
    bahan_baku = models.ForeignKey(BahanBaku, on_delete=models.CASCADE, null=True)
    quantity = models.DecimalField(max_digits=5, decimal_places=2, null=True)

class Order(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    table_number = models.IntegerField(null=True)
    quantity = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    order_type = models.CharField(choices=[('online', 'Online'), ('dine-in', 'Dine-In')], max_length=10, null=True)
    alamat = models.TextField(blank=True, null=True)
    atas_nama = models.CharField(max_length=255, null=True)
    total_price = models.IntegerField(null=True)
    status = models.CharField(choices=[('paid', 'Paid'), ('cart', 'Cart')], max_length=10, null=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

class Invoice(models.Model):
    order_item = models.ManyToManyField(Order)
    total_harga = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

class TableQr(models.Model):
    qr_code = models.TextField(blank=True, null=True)
    table_number = models.IntegerField(null=True)