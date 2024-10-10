from django.urls import path
from django.conf import settings
from . import views
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index),
    path('menu', views.management_menu),
    path('menu/add', views.form_menu),
    path('menu/edit/<int:menu_id>', views.edit_menu),
    path('menu/delete/<int:menu_id>', views.delete_menu),
    path('stock', views.management_stock),
    path('stock/add', views.form_stock),
    path('stock/edit/<int:stock_id>', views.edit_stock),
    path('stock/delete/<int:stock_id>', views.delete_stock),
    path('dashboard', views.dashboard_penjualan),
    path('table-qr', views.table_qr),
    path('table-qr/generate', views.generate_qr),
    path('table-qr/delete/<int:table_id>', views.delete_table),
    path('order/history', views.order_history),
    path('login/', auth_views.LoginView.as_view(template_name='auth-login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('order', views.order),
    path('order/delete/<int:order_id>', views.order_delete),
    path('order/<str:category>', views.order_menu, name='order_menu'),
    path('order/<str:category>/<int:table_number>/', views.order_menu, name='order_menu_with_table'),
    # path('order/dishes', views.order_menu),
    # path('order/dessert', views.order_menu),
    # path('order/beverages/<int:table_number>', views.order_beverages),
    # path('order/dishes', views.order_dishes),
    # path('order/dessert', views.order_dessert),
    # path('order/dishes/<int:table_number>', views.order_dishes),
    # path('order/dessert/<int:table_number>', views.order_dessert),
    path('cart', views.cart),
    path('checkout', views.checkout),
    path('process', views.process),
    # path('/order', views.order),
    # path('/payment', views.payment),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
