from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta, date
from store.models import *
from django.contrib.auth.models import User

def is_staff(user):
    return user.is_staff

@user_passes_test(is_staff, login_url='/accounts/login/')
def dashboard_home(request):
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_revenue = Order.objects.aggregate(Sum('total'))['total__sum'] or 0
    total_customers = User.objects.filter(is_staff=False).count()
    total_products = Service.objects.count()
    months = []
    revenue_data = []
    for i in range(11, -1, -1):
        d = timezone.now() - timedelta(days=30*i)
        rev = Order.objects.filter(created_at__year=d.year, created_at__month=d.month).aggregate(Sum('total'))['total__sum'] or 0
        months.append(d.strftime('%b'))
        revenue_data.append(float(rev))
    recent_orders = Order.objects.order_by('-created_at')[:10]
    today = timezone.now()
    week_end = today + timedelta(days=6)
    return render(request, 'dashboard/home.html', {
        'total_orders': total_orders, 'pending_orders': pending_orders,
        'total_revenue': total_revenue, 'total_customers': total_customers,
        'total_products': total_products, 'months': months,
        'revenue_data': revenue_data, 'recent_orders': recent_orders,
        'today': today, 'week_end': week_end,
    })

@user_passes_test(is_staff, login_url='/accounts/login/')
def orders_list(request):
    orders = Order.objects.order_by('-created_at')
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)
    return render(request, 'dashboard/orders.html', {'orders': orders, 'status': status})

@user_passes_test(is_staff, login_url='/accounts/login/')
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if request.method == 'POST':
        order.status = request.POST.get('status', order.status)
        order.save()
        messages.success(request, 'Order status update ho gaya!')
        return redirect('dashboard_order_detail', order_id=order_id)
    return render(request, 'dashboard/order_detail.html', {'order': order})

@user_passes_test(is_staff, login_url='/accounts/login/')
def products_list(request):
    services = Service.objects.all().order_by('-created_at')
    return render(request, 'dashboard/products.html', {'services': services})

@user_passes_test(is_staff, login_url='/accounts/login/')
def product_add(request):
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        service = Service(
            name=request.POST.get('name'),
            category_id=request.POST.get('category'),
            description=request.POST.get('description', ''),
            short_description=request.POST.get('short_description', ''),
            price=request.POST.get('price'),
            discount_price=request.POST.get('discount_price') or None,
            duration=request.POST.get('duration', ''),
            is_active=request.POST.get('is_active') == 'on',
            is_featured=request.POST.get('is_featured') == 'on',
        )
        if 'image' in request.FILES:
            service.image = request.FILES['image']
        service.save()
        messages.success(request, 'Service add ho gaya!')
        return redirect('dashboard_products')
    return render(request, 'dashboard/product_form.html', {'categories': categories, 'action': 'Add'})

@user_passes_test(is_staff, login_url='/accounts/login/')
def product_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        service.name = request.POST.get('name')
        service.category_id = request.POST.get('category')
        service.description = request.POST.get('description', '')
        service.short_description = request.POST.get('short_description', '')
        service.price = request.POST.get('price')
        service.discount_price = request.POST.get('discount_price') or None
        service.duration = request.POST.get('duration', '')
        service.is_active = request.POST.get('is_active') == 'on'
        service.is_featured = request.POST.get('is_featured') == 'on'
        if 'image' in request.FILES:
            service.image = request.FILES['image']
        service.save()
        messages.success(request, 'Service update ho gaya!')
        return redirect('dashboard_products')
    return render(request, 'dashboard/product_form.html', {'service': service, 'categories': categories, 'action': 'Edit'})

@user_passes_test(is_staff, login_url='/accounts/login/')
def product_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    messages.success(request, 'Service delete ho gaya!')
    return redirect('dashboard_products')

@user_passes_test(is_staff, login_url='/accounts/login/')
def customers_list(request):
    customers = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'dashboard/customers.html', {'customers': customers})

@user_passes_test(is_staff, login_url='/accounts/login/')
def categories_list(request):
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        cat = Category(name=name, description=request.POST.get('description', ''))
        if 'image' in request.FILES:
            cat.image = request.FILES['image']
        cat.save()
        messages.success(request, 'Category add ho gayi!')
        return redirect('dashboard_categories')
    return render(request, 'dashboard/categories.html', {'categories': categories})

@user_passes_test(is_staff, login_url='/accounts/login/')
def reviews_list(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'dashboard/reviews.html', {'reviews': reviews})

@user_passes_test(is_staff, login_url='/accounts/login/')
def coupons_list(request):
    coupons = Coupon.objects.all().order_by('-id')
    return render(request, 'dashboard/coupons.html', {'coupons': coupons})

@user_passes_test(is_staff, login_url='/accounts/login/')
def coupon_add(request):
    if request.method == 'POST':
        Coupon.objects.create(
            code=request.POST.get('code').upper(),
            discount_type=request.POST.get('discount_type'),
            discount_value=request.POST.get('discount_value'),
            min_order_amount=request.POST.get('min_order_amount', 0),
            max_uses=request.POST.get('max_uses', 100),
            is_active=request.POST.get('is_active') == 'on',
            valid_from=request.POST.get('valid_from'),
            valid_to=request.POST.get('valid_to'),
        )
        messages.success(request, 'Coupon create ho gaya!')
        return redirect('dashboard_coupons')
    return render(request, 'dashboard/coupon_form.html')

@user_passes_test(is_staff, login_url='/accounts/login/')
def analytics_view(request):
    total_revenue = Order.objects.aggregate(Sum('total'))['total__sum'] or 0
    top_services = OrderItem.objects.values('service__name').annotate(total=Count('id')).order_by('-total')[:5]
    monthly = []
    for i in range(5, -1, -1):
        d = timezone.now() - timedelta(days=30*i)
        rev = Order.objects.filter(created_at__year=d.year, created_at__month=d.month).aggregate(Sum('total'))['total__sum'] or 0
        cnt = Order.objects.filter(created_at__year=d.year, created_at__month=d.month).count()
        monthly.append({'month': d.strftime('%b %Y'), 'revenue': float(rev), 'orders': cnt})
    return render(request, 'dashboard/analytics.html', {
        'total_revenue': total_revenue, 'top_services': top_services, 'monthly': monthly
    })

@user_passes_test(is_staff, login_url='/accounts/login/')
def contacts_list(request):
    contacts = ContactQuery.objects.order_by('-created_at')
    return render(request, 'dashboard/contacts.html', {'contacts': contacts})
