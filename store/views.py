from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from django.db import IntegrityError, transaction
from .models import *
import json
import json as pyjson
from datetime import date, timedelta

# ============================================================
# Slot helpers
# ============================================================

def get_booked_slots_for_month(year, month):
    """Ek month ke saare booked slots return karo {date: [times]}"""
    from django.db.models import Q
    slots = BookingSlot.objects.filter(
        is_booked=True,
        service_date__year=year,
        service_date__month=month,
    ).values('service_date', 'service_time')

    booked = {}
    for s in slots:
        key = str(s['service_date'])
        if key not in booked:
            booked[key] = []
        booked[key].append(s['service_time'])
    return booked


def get_next_available_date(from_date=None):
    """Pehli available date find karo jahan kam se kam ek slot free ho"""
    if from_date is None:
        from_date = date.today() + timedelta(days=1)

    for i in range(60):  # max 60 din aage tak dhundo
        check_date = from_date + timedelta(days=i)
        booked_times = list(
            BookingSlot.objects.filter(
                service_date=check_date,
                is_booked=True
            ).values_list('service_time', flat=True)
        )
        # Agar saare slots booked nahi hain toh yeh date available hai
        if len(booked_times) < len(ALL_TIME_SLOTS):
            return check_date
    return None


# ============================================================
# API: Slots for a specific date (AJAX call)
# ============================================================

def get_slots_api(request):
    """
    GET /api/slots/?date=2025-04-15
    Returns: {slots: [{time, is_booked}, ...], all_booked: bool, next_available: 'YYYY-MM-DD'}
    """
    date_str = request.GET.get('date', '')
    if not date_str:
        return JsonResponse({'error': 'Date required'}, status=400)

    try:
        selected_date = date.fromisoformat(date_str)
    except ValueError:
        return JsonResponse({'error': 'Invalid date'}, status=400)

    # Minimum 1 din advance booking
    if selected_date <= date.today():
        return JsonResponse({'error': 'Aaj ya pehle ki date select nahi kar sakte'}, status=400)

    # Is date ke booked slots
    booked_times = set(
        BookingSlot.objects.filter(
            service_date=selected_date,
            is_booked=True
        ).values_list('service_time', flat=True)
    )

    slots = []
    for t in ALL_TIME_SLOTS:
        slots.append({
            'time': t,
            'is_booked': t in booked_times,
        })

    all_booked = len(booked_times) >= len(ALL_TIME_SLOTS)

    next_available = None
    if all_booked:
        next_date = get_next_available_date(selected_date + timedelta(days=1))
        if next_date:
            next_available = str(next_date)

    return JsonResponse({
        'slots': slots,
        'all_booked': all_booked,
        'next_available': next_available,
    })


# ============================================================
# Main views
# ============================================================

def home(request):
    categories = Category.objects.filter(is_active=True)
    testimonials = Testimonial.objects.filter(is_active=True)[:6]
    blogs = Blog.objects.filter(is_published=True).order_by('-created_at')[:3]
    gallery = Gallery.objects.all()[:8]
    return render(request, 'store/home.html', {
        'categories': categories,
        'testimonials': testimonials,
        'blogs': blogs,
        'gallery': gallery,
    })

def all_services(request):
    services = Service.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    total_count = services.count()
    category_slug = request.GET.get('category')
    search = request.GET.get('q')
    sort = request.GET.get('sort', '')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        services = services.filter(category=selected_category)
    if search:
        services = services.filter(Q(name__icontains=search) | Q(description__icontains=search))
    if sort == 'price_low':
        services = services.order_by('price')
    elif sort == 'price_high':
        services = services.order_by('-price')
    elif sort == 'rating':
        services = services.order_by('-rating')
    return render(request, 'store/all_services.html', {
        'services': services,
        'categories': categories,
        'selected_category': selected_category,
        'search': search,
        'sort': sort,
        'total_count': total_count,
    })

def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_active=True)
    related = Service.objects.filter(category=service.category, is_active=True).exclude(id=service.id)[:4]
    reviews = service.reviews.filter(is_approved=True).order_by('-created_at')
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    return render(request, 'store/service_detail.html', {
        'service': service, 'related': related,
        'reviews': reviews, 'avg_rating': round(avg_rating, 1)
    })

def add_to_cart(request, service_id):
    if not request.session.session_key:
        request.session.create()
    service = get_object_or_404(Service, id=service_id)
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)

    try:
        quantity = int(request.GET.get('quantity', 1))
        if quantity < 1: quantity = 1
        if quantity > 10: quantity = 10
    except:
        quantity = 1

    item, created = CartItem.objects.get_or_create(cart=cart, service=service)
    if not created:
        item.quantity += quantity
    else:
        item.quantity = quantity
    item.save()

    messages.success(request, f'"{service.name}" cart mein add ho gaya! (x{item.quantity})')
    return redirect(request.META.get('HTTP_REFERER', '/'))

def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    messages.success(request, 'Item cart se remove ho gaya.')
    return redirect('cart')

def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    qty = int(request.POST.get('quantity', 1))
    if qty > 0:
        item.quantity = qty
        item.save()
    else:
        item.delete()
    return redirect('cart')

def cart_view(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        cart = Cart.objects.filter(session_key=request.session.session_key).first()
    items = cart.items.all() if cart else []
    subtotal = sum(i.get_total() for i in items)
    discount = 0
    coupon = request.session.get('coupon')
    if coupon:
        try:
            c = Coupon.objects.get(code=coupon, is_active=True)
            if c.discount_type == 'percent':
                discount = subtotal * c.discount_value / 100
            else:
                discount = c.discount_value
        except:
            pass
    taxable_amount = subtotal - discount
    gst_amount = round(taxable_amount * 18 / 100, 2)
    total = taxable_amount + gst_amount
    return render(request, 'store/cart.html', {
        'items': items, 'subtotal': subtotal, 'discount': discount,
        'gst_amount': gst_amount, 'total': total
    })

def apply_coupon(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    try:
        coupon = Coupon.objects.get(code=code, is_active=True)
        request.session['coupon'] = code
        messages.success(request, f'Coupon "{code}" successfully apply ho gaya!')
    except:
        messages.error(request, 'Invalid ya expired coupon code.')
    return redirect('cart')


# ============================================================
# ✅ CHECKOUT VIEW — Global Slot Lock + Smart Next Date
# ============================================================
@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    items = list(cart.items.all()) if cart else []
    if not items:
        return redirect('cart')

    subtotal = sum(i.get_total() for i in items)
    discount = 0
    coupon_obj = None
    coupon_code = request.session.get('coupon')
    if coupon_code:
        try:
            coupon_obj = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon_obj.discount_type == 'percent':
                discount = subtotal * coupon_obj.discount_value / 100
            else:
                discount = coupon_obj.discount_value
        except:
            pass

    taxable = subtotal - discount
    gst_amount = round(taxable * 18 / 100, 2)
    total = taxable + gst_amount
    profile = getattr(request.user, 'profile', None)

    # Minimum booking date = kal
    min_date = date.today() + timedelta(days=1)
    # Maximum booking date = 30 din aage
    max_date = date.today() + timedelta(days=30)

    # Next available date find karo (default suggest)
    next_available = get_next_available_date(min_date)

    ctx = {
        'items': items,
        'subtotal': subtotal,
        'discount': discount,
        'gst_amount': gst_amount,
        'total': total,
        'profile': profile,
        'min_date': str(min_date),
        'max_date': str(max_date),
        'next_available_date': str(next_available) if next_available else '',
        'all_time_slots': ALL_TIME_SLOTS,
        'today': date.today(),
    }

    # ── POST: Order place karo ──
    if request.method == 'POST':
        service_date_str = request.POST.get('service_date') or None
        service_time = request.POST.get('service_time', '').strip()

        # Validation
        if not service_date_str or not service_time:
            messages.error(request, '❌ Date aur time dono select karna zaroori hai!')
            return render(request, 'store/checkout.html', ctx)

        try:
            service_date = date.fromisoformat(service_date_str)
        except ValueError:
            messages.error(request, '❌ Invalid date!')
            return render(request, 'store/checkout.html', ctx)

        if service_date <= date.today():
            messages.error(request, '❌ Minimum 1 din advance booking zaroori hai!')
            return render(request, 'store/checkout.html', ctx)

        if service_time not in ALL_TIME_SLOTS:
            messages.error(request, '❌ Invalid time slot!')
            return render(request, 'store/checkout.html', ctx)

        # ✅ Transaction + DB Lock — race condition impossible
        try:
            with transaction.atomic():

                # Global slot check — service se independent
                already_booked = BookingSlot.objects.select_for_update().filter(
                    service_date=service_date,
                    service_time=service_time,
                    is_booked=True
                ).exists()

                if already_booked:
                    # Next available slot suggest karo
                    next_date = get_next_available_date(service_date)
                    next_msg = f" Agli available date: <strong>{next_date.strftime('%d %B %Y')}</strong>" if next_date else ""
                    messages.error(
                        request,
                        f'❌ {service_date.strftime("%d %B %Y")} ko '
                        f'"{service_time}" slot already booked hai!{next_msg} '
                        f'Koi aur date/time select karein.'
                    )
                    return render(request, 'store/checkout.html', ctx)

                # Order create karo
                order = Order.objects.create(
                    user=request.user,
                    name=request.POST.get('name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    address=request.POST.get('address'),
                    city=request.POST.get('city'),
                    pincode=request.POST.get('pincode'),
                    service_date=service_date,
                    service_time=service_time,
                    special_instructions=request.POST.get('special_instructions', ''),
                    payment_method=request.POST.get('payment_method', 'cod'),
                    subtotal=subtotal,
                    discount=discount,
                    total=total,
                    coupon=coupon_obj,
                )

                # OrderItems save karo
                for item in items:
                    OrderItem.objects.create(
                        order=order,
                        service=item.service,
                        quantity=item.quantity,
                        price=item.service.get_final_price()
                    )

                # ✅ Global slot book karo — ek team = ek booking
                slot, created = BookingSlot.objects.select_for_update().get_or_create(
                    service_date=service_date,
                    service_time=service_time,
                    defaults={'order': order, 'is_booked': True}
                )

                if not created:
                    # Race condition: dono users ne simultaneously submit kiya
                    if slot.is_booked:
                        messages.error(
                            request,
                            f'❌ Yeh slot abhi kisi aur ne book kar liya! '
                            f'Koi aur time chunein.'
                        )
                        return render(request, 'store/checkout.html', ctx)
                    else:
                        slot.is_booked = True
                        slot.order = order
                        slot.save()

        except Exception as e:
            messages.error(request, '❌ Order place karne mein error aaya. Dobara try karein.')
            return render(request, 'store/checkout.html', ctx)

        # Cart clear karo
        cart.items.all().delete()
        if 'coupon' in request.session:
            del request.session['coupon']

        messages.success(request, f'✅ Order {order.order_id} successfully place ho gaya!')
        return redirect('order_success', order_id=order.order_id)

    return render(request, 'store/checkout.html', ctx)


@login_required
def book_now(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    try:
        quantity = int(request.GET.get('quantity', 1))
        if quantity < 1: quantity = 1
        if quantity > 10: quantity = 10
    except:
        quantity = 1
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart.items.all().delete()
    CartItem.objects.create(cart=cart, service=service, quantity=quantity)
    return redirect('checkout')

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'store/order_success.html', {'order': order})

@login_required
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'store/my_orders.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, 'store/order_detail.html', {'order': order})

def gallery_view(request):
    categories = Category.objects.filter(is_active=True)
    gallery = Gallery.objects.all()
    cat = request.GET.get('category')
    if cat:
        gallery = gallery.filter(category__slug=cat)
    return render(request, 'store/gallery.html', {'gallery': gallery, 'categories': categories})

def blog_list(request):
    blogs = Blog.objects.filter(is_published=True).order_by('-created_at')
    return render(request, 'store/blog_list.html', {'blogs': blogs})

def blog_detail(request, slug):
    blog = get_object_or_404(Blog, slug=slug, is_published=True)
    recent = Blog.objects.filter(is_published=True).exclude(id=blog.id)[:5]
    return render(request, 'store/blog_detail.html', {'blog': blog, 'recent': recent})

def contact(request):
    if request.method == 'POST':
        ContactQuery.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            message=request.POST.get('message'),
        )
        messages.success(request, 'Aapka message send ho gaya! Hum jald hi contact karenge.')
        return redirect('contact')
    return render(request, 'store/contact.html')

@login_required
def add_review(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    if request.method == 'POST':
        Review.objects.update_or_create(
            service=service, user=request.user,
            defaults={
                'rating': int(request.POST.get('rating', 5)),
                'comment': request.POST.get('comment', '')
            }
        )
        messages.success(request, 'Review submit ho gayi!')
    return redirect('service_detail', slug=service.slug)

def search(request):
    q = request.GET.get('q', '')
    services = Service.objects.filter(
        Q(name__icontains=q) | Q(description__icontains=q), is_active=True
    ) if q else []
    return render(request, 'store/search.html', {'services': services, 'query': q})


# ============================================================
# Invoice Downloads
# ============================================================
import io
from django.http import FileResponse, HttpResponseForbidden
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import KeepTogether


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if order.user != request.user:
        return HttpResponseForbidden("Access denied.")

    if not order.invoice_approved:
        messages.error(request, "Invoice abhi approved nahi hai. Admin ke approve karne ka wait karein.")
        return redirect('order_success', order_id=order.order_id)

    import os
    from num2words import num2words
    from django.conf import settings
    from reportlab.platypus import Image
    from reportlab.pdfgen import canvas as rl_canvas

    COMPANY_NAME  = "UTKARSH CLEANING AND HOME SERVICE"
    COMPANY_ADDR  = "Shop No 3/2 Sanskaar Bhawan\nNarela Sankri, Bhopal"
    COMPANY_PHONE = "7806061048"
    COMPANY_EMAIL = "utkarshcleaninghomeservices@gmail.com"
    COMPANY_GSTIN = "23BPEPN6081G1ZX"
    COMPANY_STATE = "23-Madhya Pradesh"
    BANK_NAME     = "CENTRAL BANK OF INDIA, NARELA SHANKARI"
    BANK_ACCOUNT  = "5924306353"
    BANK_IFSC     = "CBIN0282171"
    BANK_HOLDER   = "NARESH"
    TERMS         = "Thank you for doing business with us."
    HSN_SAC       = "998531"

    def amount_in_words(amount):
        try:
            rupees = int(amount)
            paise  = round((float(amount) - rupees) * 100)
            words  = num2words(rupees, lang='en_IN').title()
            if paise:
                words += f" and {num2words(paise, lang='en_IN').title()} Paise"
            return words + " Rupees Only"
        except:
            return ""

    subtotal   = float(order.subtotal)
    discount   = float(order.discount)
    taxable    = subtotal - discount
    gst_amount = round(taxable * 18 / 100, 2)
    total      = taxable + gst_amount
    received   = total if order.payment_status else 0.0
    balance    = total - received
    inv_number = order.order_id.replace('#', '')

    buffer = io.BytesIO()
    W, H   = A4
    c = rl_canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Invoice {inv_number}")

    margin_l = 15 * mm
    col_w    = W - 30 * mm
    margin_t = H - 15 * mm

    def draw_cell_border(x, y, w, h, fill=None, stroke_color=colors.black, stroke_width=0.5):
        c.saveState()
        c.setLineWidth(stroke_width)
        c.setStrokeColor(stroke_color)
        if fill:
            c.setFillColor(fill)
            c.rect(x, y, w, h, fill=1, stroke=1)
        else:
            c.rect(x, y, w, h, fill=0, stroke=1)
        c.restoreState()

    def text(x, y, txt, font="Helvetica", size=8, color=colors.black, align="left"):
        c.saveState()
        c.setFont(font, size)
        c.setFillColor(color)
        if align == "right":
            c.drawRightString(x, y, str(txt))
        elif align == "center":
            c.drawCentredString(x, y, str(txt))
        else:
            c.drawString(x, y, str(txt))
        c.restoreState()

    y = margin_t

    text(W / 2, y - 6*mm, "Invoice", "Helvetica-Bold", 12, align="center")
    y -= 12 * mm

    header_h = 35 * mm
    left_w   = 95 * mm
    right_w  = col_w - left_w
    draw_cell_border(margin_l, y - header_h, col_w, header_h)
    c.setLineWidth(0.5)
    c.line(margin_l + left_w, y - header_h, margin_l + left_w, y)

    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    try:
        from reportlab.platypus import Image as RLImage
        logo_img = RLImage(logo_path, width=18*mm, height=18*mm)
        logo_img.drawOn(c, margin_l + 3*mm, y - header_h + 10*mm)
    except:
        pass

    tx = margin_l + 24 * mm
    text(tx, y - 7*mm, COMPANY_NAME, "Helvetica-Bold", 9)
    addr_lines = COMPANY_ADDR.split('\n')
    for i, line in enumerate(addr_lines):
        text(tx, y - (11 + i*4)*mm, line, "Helvetica", 7.5, colors.HexColor('#333333'))
    text(tx, y - (11 + len(addr_lines)*4)*mm, f"Phone no.: {COMPANY_PHONE}", "Helvetica", 7.5, colors.HexColor('#333333'))
    text(tx, y - (15 + len(addr_lines)*4)*mm, f"Email: {COMPANY_EMAIL}", "Helvetica", 7.5, colors.HexColor('#333333'))
    text(tx, y - (19 + len(addr_lines)*4)*mm, f"GSTIN: {COMPANY_GSTIN}", "Helvetica", 7.5, colors.HexColor('#333333'))
    text(tx, y - (23 + len(addr_lines)*4)*mm, f"State: {COMPANY_STATE}", "Helvetica", 7.5, colors.HexColor('#333333'))

    rx = margin_l + left_w
    rw = right_w
    c.setLineWidth(0.5)
    c.line(rx, y - 10*mm, rx + rw, y - 10*mm)
    c.line(rx, y - 20*mm, rx + rw, y - 20*mm)
    c.line(rx + rw/2, y, rx + rw/2, y - 20*mm)
    text(rx + 2*mm, y - 5*mm, "Invoice No.", "Helvetica", 7.5, colors.HexColor('#555'))
    text(rx + 2*mm, y - 9*mm, inv_number, "Helvetica-Bold", 8)
    text(rx + rw/2 + 2*mm, y - 5*mm, "Date", "Helvetica", 7.5, colors.HexColor('#555'))
    text(rx + rw/2 + 2*mm, y - 9*mm, order.created_at.strftime("%d-%m-%Y"), "Helvetica-Bold", 8)
    text(rx + 2*mm, y - 14*mm, "Place of supply", "Helvetica", 7.5, colors.HexColor('#555'))
    text(rx + 2*mm, y - 18*mm, "23-Madhya Pradesh", "Helvetica-Bold", 8)
    y -= header_h

    bill_h = 28 * mm
    draw_cell_border(margin_l, y - bill_h, col_w, bill_h)
    text(margin_l + 2*mm, y - 4*mm,  "Bill To", "Helvetica-Bold", 8)
    text(margin_l + 2*mm, y - 9*mm,  order.name.upper(), "Helvetica-Bold", 9)
    text(margin_l + 2*mm, y - 13*mm, order.address, "Helvetica", 7.5)
    text(margin_l + 2*mm, y - 17*mm, f"{order.city}, Madhya Pradesh, India - {order.pincode}", "Helvetica", 7.5)
    text(margin_l + 2*mm, y - 22*mm, f"Phone: {order.phone}", "Helvetica", 7.5)
    text(margin_l + 2*mm, y - 26*mm, f"Email: {order.email}", "Helvetica", 7.5)
    y -= bill_h

    cols = [8*mm, 62*mm, 20*mm, 15*mm, 13*mm, 20*mm, 22*mm, 22*mm]
    col_x = [margin_l]
    for cw in cols[:-1]:
        col_x.append(col_x[-1] + cw)
    row_h = 7 * mm

    draw_cell_border(margin_l, y - row_h, col_w, row_h, fill=colors.HexColor('#f0f0f0'))
    headers = ['#', 'Item Name', 'HSN/SAC', 'Quantity', 'Unit', 'Price/Unit', 'Discount', 'Amount']
    for i, (hdr, cx) in enumerate(zip(headers, col_x)):
        if i > 0:
            c.setLineWidth(0.5)
            c.line(cx, y - row_h, cx, y)
        align = "left" if i == 1 else "center"
        tx_off = 2*mm if align == "left" else cols[i]/2
        text(cx + tx_off, y - 5*mm, hdr, "Helvetica-Bold", 7.5, align=align)
    y -= row_h

    order_items = order.items.select_related('service').all()
    for idx, item in enumerate(order_items):
        unit_price    = float(item.price)
        qty           = item.quantity
        item_amount   = unit_price * qty
        draw_cell_border(margin_l, y - row_h, col_w, row_h)
        row_data = [
            str(idx+1), item.service.name, HSN_SAC,
            str(qty), "Nos",
            f"Rs. {unit_price:,.2f}",
            "-",
            f"Rs. {item_amount:,.2f}"
        ]
        for i, (val, cx) in enumerate(zip(row_data, col_x)):
            if i > 0:
                c.setLineWidth(0.5)
                c.line(cx, y - row_h, cx, y)
            align = "left" if i == 1 else "center"
            tx_off = 2*mm if align == "left" else cols[i]/2
            text(cx + tx_off, y - 5*mm, val, "Helvetica", 7.5, align=align)
        y -= row_h

    draw_cell_border(margin_l, y - row_h, col_w, row_h, fill=colors.HexColor('#f0f0f0'))
    c.setLineWidth(0.5)
    for cx in col_x[1:]:
        c.line(cx, y - row_h, cx, y)
    text(col_x[2] + 2*mm, y - 5*mm, "Total", "Helvetica-Bold", 8)
    text(col_x[6] + cols[6]/2, y - 5*mm, f"Rs. {discount:,.2f}" if discount else "-", "Helvetica-Bold", 7.5, align="center")
    text(col_x[7] + cols[7]/2, y - 5*mm, f"Rs. {taxable:,.2f}", "Helvetica-Bold", 7.5, align="center")
    y -= row_h

    summary_left_w  = 95 * mm
    summary_right_w = col_w - summary_left_w
    summary_h       = 30 * mm
    draw_cell_border(margin_l, y - summary_h, summary_left_w, summary_h)
    draw_cell_border(margin_l + summary_left_w, y - summary_h, summary_right_w, summary_h)

    text(margin_l + 2*mm, y - 5*mm, "Invoice Amount in Words", "Helvetica-Bold", 8)
    words = amount_in_words(total)
    if len(words) > 45:
        mid = words[:45].rfind(' ')
        text(margin_l + 2*mm, y - 10*mm, words[:mid], "Helvetica", 7.5)
        text(margin_l + 2*mm, y - 14*mm, words[mid+1:], "Helvetica", 7.5)
    else:
        text(margin_l + 2*mm, y - 10*mm, words, "Helvetica", 7.5)

    rx2 = margin_l + summary_left_w
    rw2 = summary_right_w
    for offset in [8, 14, 20, 25]:
        c.setLineWidth(0.3)
        c.line(rx2, y - offset*mm, rx2 + rw2, y - offset*mm)
    lx = rx2 + 2*mm
    vx = rx2 + rw2 - 2*mm
    rows_amounts = [
        ("Amounts",    "",                      3),
        ("Sub Total",  f"Rs. {taxable:,.2f}",   7),
        ("Tax (18%)",  f"Rs. {gst_amount:,.2f}", 11),
        ("Total",      f"Rs. {total:,.2f}",     16),
        ("Received",   f"Rs. {received:,.2f}",  21),
        ("Balance",    f"Rs. {balance:,.2f}",   26),
    ]
    for label, value, offset in rows_amounts:
        fn = "Helvetica-Bold" if label in ("Amounts", "Total") else "Helvetica"
        text(lx, y - offset*mm, label, fn, 8)
        if value:
            text(vx, y - offset*mm, value, fn, 8, align="right")
    y -= summary_h

    gst_row_h = 6 * mm
    gst_cols  = [30*mm, 35*mm, 20*mm, 20*mm, 25*mm, 25*mm]
    gst_col_x = [margin_l]
    for cw in gst_cols[:-1]:
        gst_col_x.append(gst_col_x[-1] + cw)

    draw_cell_border(margin_l, y - gst_row_h, col_w, gst_row_h, fill=colors.HexColor('#f0f0f0'))
    gst_headers = ['HSN/SAC', 'Taxable Amount', 'IGST Rate', 'IGST Amt', 'Total Tax Amt', '']
    for i, (hdr, cx) in enumerate(zip(gst_headers, gst_col_x)):
        if i > 0:
            c.setLineWidth(0.5)
            c.line(cx, y - gst_row_h, cx, y)
        text(cx + gst_cols[i]/2, y - 4*mm, hdr, "Helvetica-Bold", 7, align="center")
    y -= gst_row_h

    draw_cell_border(margin_l, y - gst_row_h, col_w, gst_row_h)
    gst_data = [HSN_SAC, f"Rs. {taxable:,.2f}", "18%", f"Rs. {gst_amount:,.2f}", f"Rs. {gst_amount:,.2f}", ""]
    for i, (val, cx) in enumerate(zip(gst_data, gst_col_x)):
        if i > 0:
            c.setLineWidth(0.5)
            c.line(cx, y - gst_row_h, cx, y)
        text(cx + gst_cols[i]/2, y - 4*mm, val, "Helvetica", 7.5, align="center")
    y -= gst_row_h

    draw_cell_border(margin_l, y - gst_row_h, col_w, gst_row_h, fill=colors.HexColor('#f0f0f0'))
    for i, cx in enumerate(gst_col_x[1:], 1):
        c.setLineWidth(0.5)
        c.line(cx, y - gst_row_h, cx, y)
    text(gst_col_x[0] + gst_cols[0]/2, y - 4*mm, "Total", "Helvetica-Bold", 7.5, align="center")
    text(gst_col_x[1] + gst_cols[1]/2, y - 4*mm, f"Rs. {taxable:,.2f}", "Helvetica-Bold", 7.5, align="center")
    text(gst_col_x[3] + gst_cols[3]/2, y - 4*mm, f"Rs. {gst_amount:,.2f}", "Helvetica-Bold", 7.5, align="center")
    text(gst_col_x[4] + gst_cols[4]/2, y - 4*mm, f"Rs. {gst_amount:,.2f}", "Helvetica-Bold", 7.5, align="center")
    y -= gst_row_h

    footer_h = 35 * mm
    foot_col  = col_w / 3
    draw_cell_border(margin_l,              y - footer_h, foot_col, footer_h)
    draw_cell_border(margin_l + foot_col,   y - footer_h, foot_col, footer_h)
    draw_cell_border(margin_l + foot_col*2, y - footer_h, foot_col, footer_h)

    bx = margin_l + 2*mm
    text(bx, y - 4*mm,  "Bank Details", "Helvetica-Bold", 8)
    text(bx, y - 9*mm,  f"Name: {BANK_NAME}", "Helvetica", 7)
    text(bx, y - 13*mm, f"Account No.: {BANK_ACCOUNT}", "Helvetica", 7)
    text(bx, y - 17*mm, f"IFSC code: {BANK_IFSC}", "Helvetica", 7)
    text(bx, y - 21*mm, f"Account holder: {BANK_HOLDER}", "Helvetica", 7)

    tx2 = margin_l + foot_col + 2*mm
    text(tx2, y - 4*mm, "Terms and conditions", "Helvetica-Bold", 8)
    text(tx2, y - 9*mm, TERMS, "Helvetica", 7.5)

    sx = margin_l + foot_col*2 + 2*mm
    text(sx, y - 4*mm,  f"For: {COMPANY_NAME[:25]}", "Helvetica-Bold", 7)
    text(sx, y - 25*mm, "Authorized Signatory", "Helvetica-Bold", 7.5)

    c.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"Invoice_{inv_number}.pdf")


# ============================================================
# Dashboard Order Detail
# ============================================================
def dashboard_order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            order.status = request.POST.get('status')
            order.save()
            messages.success(request, f'Order status update ho gaya: {order.get_status_display()}')
        elif action == 'approve_invoice':
            order.invoice_approved = True
            order.save()
            messages.success(request, 'Invoice approved! Customer ab download kar sakta hai.')
        elif action == 'revoke_invoice':
            order.invoice_approved = False
            order.save()
            messages.warning(request, 'Invoice approval revoke kar diya gaya.')
        return redirect('dashboard_order_detail', order_id=order.order_id)
    return render(request, 'dashboard/order_detail.html', {'order': order})