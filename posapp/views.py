from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from decimal import Decimal
from io import BytesIO
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .forms import MenuForm, BahanBakuForm
from .models import MenuItem, BahanBaku, TableQr, Order, BahanBakuPerMenu, Invoice
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.core.paginator import Paginator
import qrcode
import base64
import json


### Query Dashboard ###

def sum_function(data, name_key, quantity_key):
    result = dict()
    for item in data:
        if item[name_key] not in result:
            result[item[name_key]] = 0
        result[item[name_key]] += int(item[quantity_key])
    return result

def most_ordered_item_query(start, end):
    data = Order.objects.filter(created_at__range=(start, end), status="Paid") \
    .values('menu_item__nama_menu') \
    .annotate(total_bought=Count('menu_item')) \
    .order_by('-total_bought')[:5]
    return data

def invoice_query(start, end):
    invoices = Invoice.objects.filter(created_at__range=(start, end))
    data = len(invoices)
    return data

def total_order_query(start, end):
    order = Order.objects.filter(created_at__range=(start, end), status="Paid")
    data = len(order)
    return data

def total_income(start, end):
    total_harga = Invoice.objects.filter(created_at__range=(start, end)).values("total_harga")
    sum_values = 0
    for d in total_harga:
        if "total_harga" in d:
            sum_values += d["total_harga"]

    return sum_values

def chart_penjualan(start, end):
    data_inv = Invoice.objects.filter(created_at__range=(start,end))

    # Group by day
    days_in_week = {}
    for invoice in data_inv:
        day = invoice.created_at.date()
        if day not in days_in_week:
            days_in_week[day] = 0
        days_in_week[day] += invoice.total_harga

    data = {
        "labels": list([key.strftime('%Y-%m-%d') for key in days_in_week.keys()]),
        "data": [float(val) for val in days_in_week.values()]

    }

    return data

def chart_penjualan_hourly(start, end):
    data_inv = Invoice.objects.filter(created_at__range=(start, end))

    # Generate a list of all hours within the range
    all_hours = [start + timedelta(hours=hour) for hour in range(round((end - start).total_seconds() / 3600) + 1)]

    # Group by hour
    hourly_data = {}
    for invoice in data_inv:
        hour = invoice.created_at.hour
        if hour not in hourly_data:
            hourly_data[hour] = 0
        hourly_data[hour] += invoice.total_harga

    # Fill in missing hours with zero values
    for hour in all_hours:
        hour_int = int(hour.hour)  # Convert hour_int to an integer
        if hour_int not in hourly_data:
            hourly_data[hour_int] = 0

    # Convert to list format
    data = {
        "labels": [f"{hour:02d}:00" for hour in sorted(hourly_data.keys())],
        "data": [hourly_data[hour] for hour in sorted(hourly_data.keys())]
    }

    return data


def total_order_permenu(start, end):
    orders_today = Order.objects.filter(
        created_at__range=[start, end]
    ).values('menu_item__nama_menu', 'quantity', 'total_price')
    testing = []
    for x in orders_today:
        testing.append({
            "nama_menu": x["menu_item__nama_menu"],
            "quantity": x["quantity"].to_decimal(),
            "total_price": x["total_price"]
        })

    result = sum_function(testing, "nama_menu", "quantity")

    return result

def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def index(request):
    return render(request, 'welcome.html')

@login_required
@user_passes_test(is_admin)
def management_menu(request):
    query = request.GET.get('q')
    if query:
        menus = MenuItem.objects.filter(nama_menu__icontains=query)
    else:
        menus = MenuItem.objects.all()
        paginator = Paginator(menus, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    return render(request, 'management-menu.html', {'datas': page_obj})

@login_required
@user_passes_test(is_admin)
def form_menu(request):
    if request.method == 'POST':
        form = MenuForm(request.POST, request.FILES)
        print(form.is_valid())
        print(form.errors)
        if form.is_valid():
            menu_instance = form.save()

            # Get lists of bahan_baku and their quantities from the form
            bahan_baku_ids = request.POST.getlist('bahan_baku')
            quantities = request.POST.getlist('quantity')

            # Iterate over the lists to create entries in BahanBakuPerMenu
            for bahan_baku_id, quantity in zip(bahan_baku_ids, quantities):
                bahan_baku = BahanBaku.objects.get(id=bahan_baku_id)
                BahanBakuPerMenu.objects.create(
                    bahan_baku=bahan_baku,
                    quantity=quantity,
                    menu_item=menu_instance
                )

            return redirect('/menu')

    # If it's a GET request, fetch all Bahan Baku data
    data_bahan_baku = BahanBaku.objects.all()
    return render(request, 'form-menu.html', {'data_bahan_baku': data_bahan_baku})


@login_required
@user_passes_test(is_admin)
def edit_menu(request, menu_id):
    data_menu = get_object_or_404(MenuItem, id=menu_id)

    if request.method == 'POST':
        form = MenuForm(request.POST, request.FILES, instance=data_menu)
        print(form.is_valid())
        if form.is_valid():
            form.save()
            return redirect('/menu')
        else:
            print(form.errors)
    else:
        form = MenuForm(instance=data_menu)
        data_bahan_baku = BahanBaku.objects.all()
        bahan_baku_per_menu = BahanBakuPerMenu.objects.filter(menu_item=data_menu)

    return render(request, 'edit-menu.html', {'form': form, 'data_bahan_baku': data_bahan_baku, 'bahan_baku_per_menu': bahan_baku_per_menu,})

@login_required
@user_passes_test(is_admin)
def delete_menu(request, menu_id):
    menu_item = get_object_or_404(MenuItem, id=menu_id)
    menu_item.delete()
    return redirect('/menu')

@login_required
@user_passes_test(is_admin)
def management_stock(request):
    query = request.GET.get('q')
    if query:
        bahan_baku = BahanBaku.objects.filter(name__icontains=query)
    else:
        bahan_baku = BahanBaku.objects.all()
        paginator = Paginator(bahan_baku, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    return render(request, 'management-stock.html', {'datas': page_obj})

@login_required
@user_passes_test(is_admin)
def edit_stock(request, stock_id):
    data_stock = get_object_or_404(BahanBaku, id=stock_id)

    if request.method == 'POST':
        form = BahanBakuForm(request.POST, instance=data_stock)
        if form.is_valid():
            form.save()
            return redirect('/stock')
    else:
        form = BahanBakuForm(instance=data_stock)

    return render(request, 'edit-stock.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def form_stock(request):
    if request.method == 'POST':
        form = BahanBakuForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/stock')

    return render(request, 'form-stock.html')

@login_required
@user_passes_test(is_admin)
def delete_stock(request, stock_id):
    stock = get_object_or_404(BahanBaku, id=stock_id)
    stock.delete()
    return redirect('/stock')

@login_required
@user_passes_test(is_admin)
def dashboard_penjualan(request, range_filter=None):
    now = timezone.now()
    if range_filter == None:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        data_penjualan = chart_penjualan_hourly(start, end)
    elif range_filter == 'weekly':
        start = now - timedelta(days=7)
        end = now
        data_penjualan = chart_penjualan(start, end)
    elif range_filter == 'monthly':
        start = now - timedelta(days=30)
        end = now
        data_penjualan = chart_penjualan(start, end)
    else:
        raise ValueError("Invalid time range. Use 'today', 'last_week', or 'last_month'.")

    data_most_menu = most_ordered_item_query(start, end)
    order_permenu = total_order_permenu(start, end)
    data_income = total_income(start, end)


    response_data = {
        "most_menu": list(data_most_menu),
        "total_inv": invoice_query(start, end),
        "total_order": total_order_query(start, end),
        "total_penjualan_permenu": order_permenu,
        "data_income": data_income,
        "chart_penjualan": data_penjualan

    }
    # print(chart_penjualan_hourly(start, end))
    return render(request, 'index.html', {'response_data': response_data})

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
    return redirect('/table-qr')

@login_required
@user_passes_test(is_admin)
def delete_table(request, table_id):
    table = get_object_or_404(TableQr, id=table_id)
    table.delete()
    return redirect('/table-qr')


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
    menu_item = order.menu_item
    quantity = order.quantity.to_decimal()

    check_stock = BahanBakuPerMenu.objects.filter(menu_item=menu_item)
    for item in check_stock:
        ingredient = item.bahan_baku
        item_quantity = item.quantity.to_decimal()
        updated_stock = ingredient.stock.to_decimal()
        updated_stock += item_quantity * quantity
        ingredient.stock = updated_stock
        ingredient.save()

    order.delete()
    return redirect('/cart')

def order_menu(request, category):
    if request.method == "POST":
        data = json.loads(request.body)
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        menu_item = MenuItem.objects.get(id=data.get("menu_item"))
        quantity = Decimal(data.get("quantity"))
        status = data.get("status")
        order_type = data.get("order_type")

        total_price = menu_item.harga.to_decimal() * quantity

        # Check stock
        check_stock = BahanBakuPerMenu.objects.filter(menu_item=menu_item)
        for item in check_stock:
            # Convert MongoDB Decimal128 to Python's Decimal
            stock_quantity = item.quantity.to_decimal()
            stock_value = item.bahan_baku.stock.to_decimal()

            # Compare stock with the required quantity
            if stock_value < stock_quantity * quantity:
                return JsonResponse({'success': False, 'message': 'Stock bahan baku habis'})

        order_data = {
            "menu_item": menu_item,
            "quantity": quantity,
            "status": status,
            "order_type": order_type,
            "session_id": session_id,
            "total_price": total_price,
        }

        if data.get("table_number"):
            order_data["table_number"] = data.get("table_number")
            order_data["order_type"] = "Dine-In"

        order = Order(**order_data)
        order.save()

        # Decrease stock for each ingredient
        for item in check_stock:
            ingredient = item.bahan_baku
            quantity_item = item.quantity.to_decimal()
            stock_decimal = ingredient.stock.to_decimal()

            # Update stock by subtracting the required quantity
            updated_stock = stock_decimal - (quantity_item * quantity)

            # Convert updated stock back to Decimal128
            ingredient.stock = Decimal(str(updated_stock))
            ingredient.save()

        return JsonResponse({'success': True, 'message': 'Item added to cart'})

    data = MenuItem.objects.filter(category=category)
    return render(request, 'guest/order.html', {'datas': data, 'category': category})


def order_guest(request, category, table_number=None):
    data = MenuItem.objects.filter(category=category)
    return render(request, 'guest/order-guest.html', {'datas': data, 'table_number': table_number, 'category': category})


def order_history(request):
    data = Order.objects.all()
    paginator = Paginator(data, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'order-history.html', {'datas': page_obj})

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
    total_price = sum(item.menu_item.harga.to_decimal() * item.quantity.to_decimal() for item in cart_items)
    return render(request, 'guest/checkout.html', {'datas': cart_items, 'harga_akhir': total_price})

def process(request):
    session_id = request.session.session_key
    cart_items = Order.objects.filter(session_id=session_id, status='Cart')
    total_price = sum(item.menu_item.harga.to_decimal() * item.quantity.to_decimal() for item in cart_items)
    invoice = Invoice.objects.create(total_harga=total_price)
    invoice.order_item.add(*cart_items)
    cart_items.update(status="Paid")


    inv_data = Order.objects.filter(invoice=invoice)

    context = {
        'datas': inv_data,
        'harga_akhir': total_price,
        'invoice_id': invoice.id,
    }

    # # Render the HTML template as a PDF
    template = get_template('guest/invoice_pdf.html')
    html = template.render(context)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    # Create a PDF from the HTML
    pisa_status = pisa.CreatePDF(html, dest=response)

    # If there is an error, show it in the browser
    if pisa_status.err:
        return HttpResponse('We had some errors with generating your invoice PDF.')

    return response