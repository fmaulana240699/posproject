from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from io import BytesIO
from .forms import MenuForm, BahanBakuForm
from .models import MenuItem, BahanBaku, TableQr, Order
import qrcode
import base64
import json

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def index(request):
    return render(request, 'index.html')

@login_required
@user_passes_test(is_admin)
def management_menu(request):
    menus = MenuItem.objects.all()
    return render(request, 'management-menu.html', {'datas': menus})

@login_required
@user_passes_test(is_admin)
def form_menu(request):
    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')

    return render(request, 'form-menu.html')

@login_required
@user_passes_test(is_admin)
def edit_menu(request, menu_id):
    # Fetch the product from the database
    data_menu = get_object_or_404(MenuItem, id=menu_id)

    if request.method == 'POST':
        # Populate the form with the POST data and the existing instance
        form = MenuForm(request.POST, instance=data_menu)
        if form.is_valid():
            form.save()  # This will update the existing product in the database
            return redirect('/')  # Redirect to the list or success page
    else:
        # Prepopulate the form with existing data
        form = MenuForm(instance=data_menu)

    return render(request, 'edit-menu.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def delete_menu(request, menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)

    # if request.method == 'POST':
    menu_item.delete()
    return redirect('/')

@login_required
@user_passes_test(is_admin)
def management_stock(request):
    bahan_baku = BahanBaku.objects.all()
    return render(request, 'management-stock.html', {'datas': bahan_baku})

@login_required
@user_passes_test(is_admin)
def edit_stock(request, stock_id):
    # Fetch the product from the database
    data_stock = get_object_or_404(BahanBaku, id=stock_id)

    if request.method == 'POST':
        # Populate the form with the POST data and the existing instance
        form = BahanBakuForm(request.POST, instance=data_stock)
        if form.is_valid():
            form.save()  # This will update the existing product in the database
            return redirect('/')  # Redirect to the list or success page
    else:
        # Prepopulate the form with existing data
        form = BahanBakuForm(instance=data_stock)

    return render(request, 'edit-stock.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def form_stock(request):
    if request.method == 'POST':
        form = BahanBakuForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')

    return render(request, 'form-stock.html')

@login_required
@user_passes_test(is_admin)
def delete_stock(request, stock_id):
    stock = get_object_or_404(BahanBaku, id=stock_id)

    # if request.method == 'POST':
    stock.delete()
    return redirect('/')

@login_required
@user_passes_test(is_admin)
def dashboard_penjualan(request):
    return render(request, 'index.html')

@login_required
@user_passes_test(is_admin)
def table_qr(request):
    data = TableQr.objects.all()
    return render(request, 'table-qr.html', {'datas': data})

@login_required
@user_passes_test(is_admin)
def generate_qr(request):
    table_number = request.POST.get("table_number")
    table = TableQr.objects.create(table_number=table_number)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(f'http://localhost:8000/order/{table_number}')
    qr.make(fit=True)

    # Get QR code data as a string
    img = qr.make_image(fill_color="black", back_color="white")

    # Save QR code data as bytes
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    table.qr_code=base64_image
    table.save()
    return redirect('/')

@login_required
@user_passes_test(is_admin)
def delete_table(request, table_id):
    table = get_object_or_404(TableQr, id=table_id)
    table.delete()
    return redirect('/')


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            error_message = "Invalid username or password."

    return render(request, 'auth-login.html', {'error_message': error_message if 'error_message' in locals() else ''})


def logout_view(request):
    logout(request)
    return redirect('login')

##########################
##### Guest Side #########
#########################

def order(request):
    return render(request, 'guest/index.html')

def order_delete(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect('/cart')

def order_menu(request, category, table_number=None):
    if request.method == "POST":
        data = json.loads(request.body)
        session_id = request.session.session_key
        if not session_id:
            request.session.create()  # Create a session if it doesn't exist
            session_id = request.session.session_key
        menu_item = MenuItem.objects.get(id=data.get("menu_item"))
        quantity = data.get("quantity")
        status = data.get("status")
        order_type = data.get("order_type")

        total_price = menu_item.harga * quantity

        order_data = {
            "menu_item": menu_item,
            "quantity": quantity,
            "status": status,
            "order_type": order_type,
            "session_id": session_id,
            "total_price": total_price,
            }

        if data.get("table_number") != "None":
            order_data["table_number"]=data.get("table_number")
            order_data["order_type"] = "Dine-In"

        order = Order(**order_data)
        order.save()

        return JsonResponse({'success': True, 'message': 'Item added to cart'})

    data = MenuItem.objects.filter(category=category)
    return render(request, 'guest/order.html', {'datas': data, 'table_number': table_number, 'category': category})

def order_history(request):
    data = Order.objects.all()
    return render(request, 'order-history.html', {'datas': data})

# def order_dishes(request, table_number=None):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         session_id = request.session.session_key
#         if not session_id:
#             request.session.create()  # Create a session if it doesn't exist
#             session_id = request.session.session_key
#         menu_item = MenuItem.objects.get(id=data.get("menu_item"))
#         quantity = data.get("quantity")
#         status = data.get("status")
#         order_type = data.get("order_type")

#         total_price = menu_item.harga * quantity

#         order_data = {
#             "menu_item": menu_item,
#             "quantity": quantity,
#             "status": status,
#             "order_type": order_type,
#             "session_id": session_id,
#             "total_price": total_price,
#             }

#         if data.get("table_number") != "None":
#             order_data["table_number"]=data.get("table_number")
#             order_data["order_type"] = "Dine-In"

#         order = Order(**order_data)
#         order.save()

#         return JsonResponse({'success': True, 'message': 'Item added to cart'})

#     data = MenuItem.objects.filter(category="dishes")
#     return render(request, 'guest/dishes.html', {'datas': data, 'table_number': table_number})

# def order_dessert(request, table_number=None):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         session_id = request.session.session_key
#         if not session_id:
#             request.session.create()  # Create a session if it doesn't exist
#             session_id = request.session.session_key
#         menu_item = MenuItem.objects.get(id=data.get("menu_item"))
#         quantity = data.get("quantity")
#         status = data.get("status")
#         order_type = data.get("order_type")

#         total_price = menu_item.harga * quantity

#         order_data = {
#             "menu_item": menu_item,
#             "quantity": quantity,
#             "status": status,
#             "order_type": order_type,
#             "session_id": session_id,
#             "total_price": total_price,
#             }

#         if data.get("table_number") != "None":
#             order_data["table_number"]=data.get("table_number")
#             order_data["order_type"] = "Dine-In"

#         order = Order(**order_data)
#         order.save()

#         return JsonResponse({'success': True, 'message': 'Item added to cart'})

#     data = MenuItem.objects.filter(category="dishes")
#     return render(request, 'guest/dessert.html', {'datas': data, 'table_number': table_number})

def cart(request):
    session_id = request.session.session_key
    cart_items = Order.objects.filter(session_id=session_id, status='Cart')
    return render(request, 'guest/cart.html', {'datas': cart_items})

def checkout(request):
    if request.method == "POST":
        session_id = request.session.session_key
        cart_items = Order.objects.filter(session_id=session_id, status='Cart')

        order_data={
            "atas_nama": request.POST.get("atas_nama"),
            "alamat": request.POST.get("alamat")
        }

        cart_items.update(**order_data)
        return redirect('/checkout')

    session_id = request.session.session_key
    cart_items = Order.objects.filter(session_id=session_id, status='Cart')
    total_price = sum(item.menu_item.harga * item.quantity for item in cart_items)
    return render(request, 'guest/checkout.html', {'datas': cart_items, 'harga_akhir': total_price})

def process(request):
    session_id = request.session.session_key
    cart_items = Order.objects.filter(session_id=session_id, status='Cart')
    cart_items.update(status="Paid")
    return redirect("/")