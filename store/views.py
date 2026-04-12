from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg
from .models import *
import json

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

# def add_to_cart(request, service_id):
#     if not request.session.session_key:
#         request.session.create()
#     service = get_object_or_404(Service, id=service_id)
#     if request.user.is_authenticated:
#         cart, _ = Cart.objects.get_or_create(user=request.user)
#     else:
#         cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)
#     item, created = CartItem.objects.get_or_create(cart=cart, service=service)
#     if not created:
#         item.quantity += 1
#         item.save()
#     messages.success(request, f'"{service.name}" cart mein add ho gaya!')
#     return redirect(request.META.get('HTTP_REFERER', '/'))
def add_to_cart(request, service_id):
    if not request.session.session_key:
        request.session.create()
    service = get_object_or_404(Service, id=service_id)
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key)

    # Quantity GET param se lo (bathroom category ke liye), default 1
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

# def cart_view(request):
#     if request.user.is_authenticated:
#         cart = Cart.objects.filter(user=request.user).first()
#     else:
#         cart = Cart.objects.filter(session_key=request.session.session_key).first()
#     items = cart.items.all() if cart else []
#     subtotal = sum(i.get_total() for i in items)
#     discount = 0
#     coupon = request.session.get('coupon')
#     if coupon:
#         try:
#             c = Coupon.objects.get(code=coupon, is_active=True)
#             if c.discount_type == 'percent':
#                 discount = subtotal * c.discount_value / 100
#             else:
#                 discount = c.discount_value
#         except:
#             pass
#     total = subtotal - discount
#     return render(request, 'store/cart.html', {
#         'items': items, 'subtotal': subtotal, 'discount': discount, 'total': total
#     })

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
    gst_amount = round(taxable_amount * 18 / 100, 2)   # 18% GST
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

# @login_required
# def checkout(request):
#     cart = Cart.objects.filter(user=request.user).first()
#     items = cart.items.all() if cart else []
#     if not items:
#         return redirect('cart')
#     subtotal = sum(i.get_total() for i in items)
#     discount = 0
#     coupon_obj = None
#     coupon_code = request.session.get('coupon')
#     if coupon_code:
#         try:
#             coupon_obj = Coupon.objects.get(code=coupon_code, is_active=True)
#             if coupon_obj.discount_type == 'percent':
#                 discount = subtotal * coupon_obj.discount_value / 100
#             else:
#                 discount = coupon_obj.discount_value
#         except:
#             pass
#     total = subtotal - discount
#     profile = getattr(request.user, 'profile', None)
#     if request.method == 'POST':
#         order = Order.objects.create(
#             user=request.user,
#             name=request.POST.get('name'),
#             email=request.POST.get('email'),
#             phone=request.POST.get('phone'),
#             address=request.POST.get('address'),
#             city=request.POST.get('city'),
#             pincode=request.POST.get('pincode'),
#             service_date=request.POST.get('service_date') or None,
#             service_time=request.POST.get('service_time', ''),
#             special_instructions=request.POST.get('special_instructions', ''),
#             payment_method=request.POST.get('payment_method', 'cod'),
#             subtotal=subtotal, discount=discount, total=total, coupon=coupon_obj,
#         )
#         for item in items:
#             OrderItem.objects.create(order=order, service=item.service, quantity=item.quantity, price=item.service.get_final_price())
#         cart.items.all().delete()
#         if 'coupon' in request.session:
#             del request.session['coupon']
#         messages.success(request, f'Order {order.order_id} successfully place ho gaya!')
#         return redirect('order_success', order_id=order.order_id)
#     return render(request, 'store/checkout.html', {
#         'items': items, 'subtotal': subtotal, 'discount': discount, 'total': total, 'profile': profile
#     })

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    items = cart.items.all() if cart else []
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

    # ✅ GST 18% add kiya
    gst_amount = round((subtotal - discount) * 18 / 100, 2)
    total = subtotal - discount + gst_amount

    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        order = Order.objects.create(
            user=request.user,
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            address=request.POST.get('address'),
            city=request.POST.get('city'),
            pincode=request.POST.get('pincode'),
            service_date=request.POST.get('service_date') or None,
            service_time=request.POST.get('service_time', ''),
            special_instructions=request.POST.get('special_instructions', ''),
            payment_method=request.POST.get('payment_method', 'cod'),
            subtotal=subtotal, discount=discount, total=total, coupon=coupon_obj,
        )
        for item in items:
            OrderItem.objects.create(order=order, service=item.service, quantity=item.quantity, price=item.service.get_final_price())
        cart.items.all().delete()
        if 'coupon' in request.session:
            del request.session['coupon']
        messages.success(request, f'Order {order.order_id} successfully place ho gaya!')
        return redirect('order_success', order_id=order.order_id)

    return render(request, 'store/checkout.html', {
        'items': items, 'subtotal': subtotal, 'discount': discount,
        'gst_amount': gst_amount, 'total': total, 'profile': profile  # ✅ gst_amount bhi pass kiya
    })





# @login_required
# def book_now(request, service_id):
#     service = get_object_or_404(Service, id=service_id)
#     # Pehle cart clear karo aur sirf yahi service daalo
#     cart, _ = Cart.objects.get_or_create(user=request.user)
#     cart.items.all().delete()  # purani items hataao
#     CartItem.objects.create(cart=cart, service=service, quantity=1)
#     return redirect('checkout')



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
            defaults={'rating': int(request.POST.get('rating', 5)), 'comment': request.POST.get('comment', '')}
        )
        messages.success(request, 'Review submit ho gayi!')
    return redirect('service_detail', slug=service.slug)

def search(request):
    q = request.GET.get('q', '')
    services = Service.objects.filter(Q(name__icontains=q) | Q(description__icontains=q), is_active=True) if q else []
    return render(request, 'store/search.html', {'services': services, 'query': q})













import io
from django.http import FileResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.platypus import KeepTogether

# ── Import your models (adjust path if needed) ──
from .models import Order


@login_required
def download_invoice(request, order_id):
    """
    Generate and return a professional PDF invoice for the given order.
    Only the order owner can download it.
    """
    order = get_object_or_404(Order, order_id=order_id)

    # Security: only the order owner can download
    if order.user != request.user:
        return HttpResponseForbidden("Access denied.")

    # ── Build PDF in memory ──
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm,
    )

    W, H = A4
    story = []

    # ════════════════════════════════════════
    #  COLORS
    # ════════════════════════════════════════
    NAVY      = colors.HexColor('#0a1628')
    GOLD      = colors.HexColor('#c9a84c')
    LIGHT_BG  = colors.HexColor('#f4f8ff')
    MUTED     = colors.HexColor('#7a8ba0')
    WHITE     = colors.white
    GREEN     = colors.HexColor('#27ae60')
    RED       = colors.HexColor('#e74c3c')

    # ════════════════════════════════════════
    #  STYLES
    # ════════════════════════════════════════
    styles = getSampleStyleSheet()

    def style(name, **kwargs):
        return ParagraphStyle(name, **kwargs)

    s_company = style('company',
        fontName='Helvetica-Bold', fontSize=22,
        textColor=WHITE, alignment=TA_LEFT)

    s_company_sub = style('company_sub',
        fontName='Helvetica', fontSize=9,
        textColor=colors.HexColor('#b0c4de'), alignment=TA_LEFT)

    s_invoice_label = style('inv_label',
        fontName='Helvetica', fontSize=9,
        textColor=MUTED, alignment=TA_RIGHT)

    s_invoice_value = style('inv_value',
        fontName='Helvetica-Bold', fontSize=11,
        textColor=NAVY, alignment=TA_RIGHT)

    s_section_title = style('sec_title',
        fontName='Helvetica-Bold', fontSize=10,
        textColor=GOLD, spaceAfter=4)

    s_normal = style('s_normal',
        fontName='Helvetica', fontSize=9,
        textColor=NAVY, leading=14)

    s_bold = style('s_bold',
        fontName='Helvetica-Bold', fontSize=9,
        textColor=NAVY)

    s_muted = style('s_muted',
        fontName='Helvetica', fontSize=8,
        textColor=MUTED)

    s_total_label = style('total_label',
        fontName='Helvetica-Bold', fontSize=11,
        textColor=WHITE, alignment=TA_RIGHT)

    s_total_value = style('total_value',
        fontName='Helvetica-Bold', fontSize=13,
        textColor=GOLD, alignment=TA_RIGHT)

    s_thank = style('thank',
        fontName='Helvetica-Bold', fontSize=13,
        textColor=NAVY, alignment=TA_CENTER)

    s_footer = style('footer',
        fontName='Helvetica', fontSize=8,
        textColor=MUTED, alignment=TA_CENTER)

    # ════════════════════════════════════════
    #  HEADER — Navy banner with company name
    # ════════════════════════════════════════
    status_color = GREEN if order.payment_status else RED
    status_text  = 'PAID' if order.payment_status else 'UNPAID'

    header_data = [
        [
            Paragraph('UTKARSH', s_company),
            Paragraph(f'<font color="#c9a84c"><b>TAX INVOICE</b></font>', style('inv_big',
                fontName='Helvetica-Bold', fontSize=18,
                textColor=GOLD, alignment=TA_RIGHT)),
        ],
        [
            Paragraph('Cleaning &amp; Home Services<br/>Bhopal, Madhya Pradesh', s_company_sub),
            Paragraph(
                f'Order ID: <b>{order.order_id}</b><br/>'
                f'Date: <b>{order.created_at.strftime("%d %b %Y")}</b><br/>'
                f'Status: <font color="{"#27ae60" if order.payment_status else "#e74c3c"}"><b>{status_text}</b></font>',
                style('inv_meta', fontName='Helvetica', fontSize=9,
                      textColor=WHITE, alignment=TA_RIGHT)
            ),
        ],
    ]

    header_table = Table(header_data, colWidths=[90*mm, 85*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), NAVY),
        ('TOPPADDING',    (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LEFTPADDING',   (0,0), (0,-1), 12),
        ('RIGHTPADDING',  (-1,0),(-1,-1), 12),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS',(0,0), (-1,-1), [NAVY]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6*mm))

    # ════════════════════════════════════════
    #  BILLED TO  +  SERVICE INFO  (two cols)
    # ════════════════════════════════════════
    def info_block(title, lines):
        """Returns a list of Paragraphs for an info block."""
        block = [Paragraph(title, s_section_title)]
        for line in lines:
            block.append(Paragraph(line, s_normal))
        return block

    billed_lines = [
        f'<b>{order.name}</b>',
        order.address,
        f'{order.city} - {order.pincode}',
        f'Phone: {order.phone}',
        f'Email: {order.email}',
    ]

    service_lines = [
        f'<b>Service Date:</b> {order.service_date.strftime("%d %b %Y") if order.service_date else "—"}',
        f'<b>Service Time:</b> {order.service_time or "—"}',
        f'<b>Payment Method:</b> {order.get_payment_method_display()}',
        f'<b>Order Status:</b> {order.get_status_display()}',
    ]
    if order.special_instructions:
        service_lines.append(f'<b>Notes:</b> {order.special_instructions[:80]}')

    def col_table(left_items, right_items):
        left_cell  = left_items
        right_cell = right_items
        t = Table([[left_cell, right_cell]], colWidths=[87*mm, 88*mm])
        t.setStyle(TableStyle([
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
            ('LEFTPADDING',   (0,0),(0,-1),  0),
            ('RIGHTPADDING',  (0,0),(0,-1),  8),
            ('LEFTPADDING',   (1,0),(1,-1),  8),
        ]))
        return t

    story.append(col_table(
        info_block('BILLED TO', billed_lines),
        info_block('SERVICE DETAILS', service_lines),
    ))
    story.append(Spacer(1, 5*mm))
    story.append(HRFlowable(width='100%', thickness=0.5, color=MUTED))
    story.append(Spacer(1, 4*mm))

    # ════════════════════════════════════════
    #  ITEMS TABLE
    # ════════════════════════════════════════
    story.append(Paragraph('SERVICES BOOKED', s_section_title))
    story.append(Spacer(1, 2*mm))

    # Header row
    col_widths = [10*mm, 85*mm, 20*mm, 22*mm, 28*mm]
    th_style = ParagraphStyle('th', fontName='Helvetica-Bold',
                               fontSize=9, textColor=WHITE, alignment=TA_CENTER)
    th_left  = ParagraphStyle('th_left', fontName='Helvetica-Bold',
                               fontSize=9, textColor=WHITE, alignment=TA_LEFT)

    table_data = [[
        Paragraph('#',            th_style),
        Paragraph('Service Name', th_left),
        Paragraph('Qty',          th_style),
        Paragraph('Unit Price',   th_style),
        Paragraph('Amount',       th_style),
    ]]

    # Data rows
    td_center = ParagraphStyle('td_c', fontName='Helvetica', fontSize=9,
                                textColor=NAVY, alignment=TA_CENTER)
    td_left   = ParagraphStyle('td_l', fontName='Helvetica', fontSize=9,
                                textColor=NAVY, alignment=TA_LEFT)
    td_right  = ParagraphStyle('td_r', fontName='Helvetica', fontSize=9,
                                textColor=NAVY, alignment=TA_RIGHT)
    td_bold_r = ParagraphStyle('td_br', fontName='Helvetica-Bold', fontSize=9,
                                textColor=NAVY, alignment=TA_RIGHT)

    order_items = order.items.select_related('service').all()
    row_colors  = [LIGHT_BG, WHITE]

    for idx, item in enumerate(order_items, 1):
        unit_price = float(item.price)
        total_price = float(item.get_total())
        table_data.append([
            Paragraph(str(idx),                    td_center),
            Paragraph(item.service.name,           td_left),
            Paragraph(str(item.quantity),          td_center),
            Paragraph(f'Rs. {unit_price:,.2f}',    td_right),
            Paragraph(f'Rs. {total_price:,.2f}',   td_bold_r),
        ])

    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    item_style = [
        # Header
        ('BACKGROUND',    (0,0), (-1,0), NAVY),
        ('ROWBACKGROUNDS',(0,1), (-1,-1), [LIGHT_BG, WHITE]),
        ('GRID',          (0,0), (-1,-1), 0.3, colors.HexColor('#dce6f5')),
        ('LINEBELOW',     (0,0), (-1,0),  1.5, GOLD),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING',   (0,0), (-1,-1), 6),
        ('RIGHTPADDING',  (0,0), (-1,-1), 6),
        ('VALIGN',        (0,0), (-1,-1), 'MIDDLE'),
    ]
    items_table.setStyle(TableStyle(item_style))
    story.append(items_table)
    story.append(Spacer(1, 5*mm))

    # ════════════════════════════════════════
    #  TOTALS BLOCK
    # ════════════════════════════════════════
    def amount_row(label, value, bold=False, highlight=False):
        lbl_style = ParagraphStyle('lbl', fontName='Helvetica-Bold' if bold else 'Helvetica',
                                    fontSize=10 if bold else 9,
                                    textColor=WHITE if highlight else NAVY,
                                    alignment=TA_RIGHT)
        val_style = ParagraphStyle('val', fontName='Helvetica-Bold',
                                    fontSize=12 if bold else 9,
                                    textColor=GOLD if highlight else NAVY,
                                    alignment=TA_RIGHT)
        row = [[Paragraph(label, lbl_style), Paragraph(value, val_style)]]
        t = Table(row, colWidths=[110*mm, 55*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), NAVY if highlight else colors.transparent),
            ('TOPPADDING',    (0,0),(-1,-1), 5 if bold else 3),
            ('BOTTOMPADDING', (0,0),(-1,-1), 5 if bold else 3),
            ('RIGHTPADDING',  (0,0),(-1,-1), 6),
            ('LINEABOVE',     (0,0),(-1,0),  0.5 if bold else 0, MUTED),
        ]))
        return t

    subtotal_val = float(order.subtotal)
    discount_val = float(order.discount)
    total_val    = float(order.total)

    story.append(amount_row('Subtotal', f'Rs. {subtotal_val:,.2f}'))
    if discount_val > 0:
        story.append(amount_row('Discount (Coupon)', f'- Rs. {discount_val:,.2f}'))
    if order.coupon:
        story.append(amount_row(f'Coupon Code: {order.coupon.code}', ''))
    story.append(Spacer(1, 2*mm))
    story.append(amount_row('TOTAL AMOUNT', f'Rs. {total_val:,.2f}', bold=True, highlight=True))

    story.append(Spacer(1, 8*mm))

    # ════════════════════════════════════════
    #  THANK YOU + FOOTER
    # ════════════════════════════════════════
    story.append(HRFlowable(width='100%', thickness=1, color=GOLD))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph('Thank You for Choosing Utkarsh Cleaning Services!', s_thank))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        'For support: <b>+91-XXXXXXXXXX</b> &nbsp;|&nbsp; '
        'utkarshcleaning@email.com &nbsp;|&nbsp; Bhopal, MP',
        s_footer
    ))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        'This is a computer-generated invoice and does not require a physical signature.',
        s_footer
    ))

    # ── Build ──
    doc.build(story)
    buffer.seek(0)

    filename = f"Invoice_{order.order_id.replace('#','')}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)











































@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if order.user != request.user:
        return HttpResponseForbidden("Access denied.")

    if not order.invoice_approved:
        messages.error(request, "Invoice abhi approved nahi hai. Admin ke approve karne ka wait karein.")
        return redirect('order_success', order_id=order.order_id)

    import io
    import os
    from num2words import num2words
    from django.conf import settings
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas as rl_canvas

    # ── Constants ──
    COMPANY_NAME    = "UTKARSH CLEANING AND HOME SERVICE"
    COMPANY_ADDR    = "Shop No 3/2 Sanskaar Bhawan\nNarela Sankri, Bhopal"
    COMPANY_PHONE   = "7806061048"
    COMPANY_EMAIL   = "utkarshcleaninghomeservices@gmail.com"
    COMPANY_GSTIN   = "23BPEPN6081G1ZX"
    COMPANY_STATE   = "23-Madhya Pradesh"
    BANK_NAME       = "CENTRAL BANK OF INDIA, NARELA SHANKARI"
    BANK_ACCOUNT    = "5924306353"
    BANK_IFSC       = "CBIN0282171"
    BANK_HOLDER     = "NARESH"
    TERMS           = "Thank you for doing business with us."
    HSN_SAC         = "998531"

    # ── Amount in words helper ──
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

    # ── Calculate amounts ──
    subtotal     = float(order.subtotal)
    discount     = float(order.discount)
    taxable      = subtotal - discount
    gst_amount   = round(taxable * 18 / 100, 2)
    total        = taxable + gst_amount
    received     = total if order.payment_status else 0.0
    balance      = total - received

    # ── Invoice number (sequential-style from order_id) ──
    inv_number = order.order_id.replace('#', '')

    # ── Build PDF ──
    buffer = io.BytesIO()
    W, H   = A4

    # Use canvas for pixel-perfect layout
    c = rl_canvas.Canvas(buffer, pagesize=A4)
    c.setTitle(f"Invoice {inv_number}")

    margin_l = 15 * mm
    margin_r = W - 15 * mm
    margin_t = H - 15 * mm
    col_w    = W - 30 * mm   # usable width

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

    y = margin_t  # current y position (top to bottom)

    # ══════════════════════════════════════
    #  TITLE
    # ══════════════════════════════════════
    text(W / 2, y - 6*mm, "Invoice", "Helvetica-Bold", 12, align="center")
    y -= 12 * mm

    # ══════════════════════════════════════
    #  HEADER BOX — Logo+Company | Invoice No+Date
    # ══════════════════════════════════════
    header_h = 35 * mm
    left_w   = 95 * mm
    right_w  = col_w - left_w

    # outer box
    draw_cell_border(margin_l, y - header_h, col_w, header_h)

    # vertical divider
    c.setLineWidth(0.5)
    c.line(margin_l + left_w, y - header_h, margin_l + left_w, y)

    # Logo
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    try:
        logo_img = Image(logo_path, width=18*mm, height=18*mm)
        logo_img.drawOn(c, margin_l + 3*mm, y - header_h + 10*mm)
    except:
        pass  # logo nahi mila toh skip

    # Company info
    tx = margin_l + 24 * mm
    text(tx, y - 7*mm,  COMPANY_NAME,   "Helvetica-Bold", 9)
    addr_lines = COMPANY_ADDR.split('\n')
    for i, line in enumerate(addr_lines):
        text(tx, y - (11 + i*4)*mm, line, "Helvetica", 7.5, colors.HexColor('#333333'))
    text(tx, y - (11 + len(addr_lines)*4)*mm, f"Phone no.: {COMPANY_PHONE}", "Helvetica", 7.5, colors.HexColor('#333333'))
    text(tx, y - (15 + len(addr_lines)*4)*mm, f"Email: {COMPANY_EMAIL}", "Helvetica", 7.5, colors.HexColor('#333333'))
    text(tx, y - (19 + len(addr_lines)*4)*mm, f"GSTIN: {COMPANY_GSTIN}", "Helvetica", 7.5, colors.HexColor('#333333'))
    text(tx, y - (23 + len(addr_lines)*4)*mm, f"State: {COMPANY_STATE}", "Helvetica", 7.5, colors.HexColor('#333333'))

    # Right side: Invoice No / Date / Place of supply
    rx = margin_l + left_w
    rw = right_w

    # horizontal lines inside right box
    c.setLineWidth(0.5)
    c.line(rx, y - 10*mm, rx + rw, y - 10*mm)
    c.line(rx, y - 20*mm, rx + rw, y - 20*mm)
    c.line(rx + rw/2, y, rx + rw/2, y - 20*mm)  # vertical split for top 2 rows

    text(rx + 2*mm, y - 5*mm,  "Invoice No.",      "Helvetica",      7.5, colors.HexColor('#555'))
    text(rx + 2*mm, y - 9*mm,  inv_number,          "Helvetica-Bold", 8)
    text(rx + rw/2 + 2*mm, y - 5*mm, "Date",         "Helvetica",      7.5, colors.HexColor('#555'))
    text(rx + rw/2 + 2*mm, y - 9*mm, order.created_at.strftime("%d-%m-%Y"), "Helvetica-Bold", 8)

    text(rx + 2*mm, y - 14*mm, "Place of supply",   "Helvetica",      7.5, colors.HexColor('#555'))
    text(rx + 2*mm, y - 18*mm, "23-Madhya Pradesh", "Helvetica-Bold", 8)

    y -= header_h

    # ══════════════════════════════════════
    #  BILL TO
    # ══════════════════════════════════════
    bill_h = 28 * mm
    draw_cell_border(margin_l, y - bill_h, col_w, bill_h)

    text(margin_l + 2*mm, y - 4*mm,  "Bill To",          "Helvetica-Bold", 8)
    text(margin_l + 2*mm, y - 9*mm,  order.name.upper(), "Helvetica-Bold", 9)
    text(margin_l + 2*mm, y - 13*mm, order.address,      "Helvetica",      7.5)
    text(margin_l + 2*mm, y - 17*mm, f"{order.city}, Madhya Pradesh, India - {order.pincode}", "Helvetica", 7.5)
    text(margin_l + 2*mm, y - 22*mm, f"Phone: {order.phone}", "Helvetica", 7.5)
    text(margin_l + 2*mm, y - 26*mm, f"Email: {order.email}", "Helvetica", 7.5)

    y -= bill_h

    # ══════════════════════════════════════
    #  ITEMS TABLE HEADER
    # ══════════════════════════════════════
    # Column widths (mm): #=8, Item=65, HSN=20, Qty=15, Unit=12, Price=20, Disc=22, Amt=22 → total=184
    cols = [8*mm, 62*mm, 20*mm, 15*mm, 13*mm, 20*mm, 22*mm, 22*mm]
    col_x = [margin_l]
    for cw in cols[:-1]:
        col_x.append(col_x[-1] + cw)

    row_h = 7 * mm

    # Header row fill
    draw_cell_border(margin_l, y - row_h, col_w, row_h, fill=colors.HexColor('#f0f0f0'))

    headers = ['#', 'Item Name', 'HSN/SAC', 'Quantity', 'Unit', 'Price/Unit', 'Discount', 'Amount']
    for i, (hdr, cx) in enumerate(zip(headers, col_x)):
        # vertical line
        if i > 0:
            c.setLineWidth(0.5)
            c.line(cx, y - row_h, cx, y)
        align = "left" if i == 1 else "center"
        tx_off = 2*mm if align == "left" else cols[i]/2
        text(cx + tx_off, y - 5*mm, hdr, "Helvetica-Bold", 7.5, align=align)

    y -= row_h

    # ── Item rows ──
    order_items = order.items.select_related('service').all()
    for idx, item in enumerate(order_items):
        unit_price   = float(item.price)
        qty          = item.quantity
        item_subtotal = unit_price * qty
        item_discount = 0.0   # per-item discount (0 for now)
        item_amount   = item_subtotal - item_discount

        draw_cell_border(margin_l, y - row_h, col_w, row_h)
        row_data = [
            str(idx+1), item.service.name, HSN_SAC,
            str(qty), "Nos",
            f"Rs. {unit_price:,.2f}",
            f"Rs. {item_discount:,.2f}" if item_discount else "-",
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

    # ══════════════════════════════════════
    #  TOTAL ROW
    # ══════════════════════════════════════
    draw_cell_border(margin_l, y - row_h, col_w, row_h, fill=colors.HexColor('#f0f0f0'))
    c.setLineWidth(0.5)
    for cx in col_x[1:]:
        c.line(cx, y - row_h, cx, y)
    text(col_x[2] + 2*mm, y - 5*mm, "Total", "Helvetica-Bold", 8)
    # discount total
    text(col_x[6] + cols[6]/2, y - 5*mm,
         f"Rs. {discount:,.2f}" if discount else "-", "Helvetica-Bold", 7.5, align="center")
    text(col_x[7] + cols[7]/2, y - 5*mm,
         f"Rs. {taxable:,.2f}", "Helvetica-Bold", 7.5, align="center")
    y -= row_h

    # ══════════════════════════════════════
    #  AMOUNT IN WORDS + AMOUNTS SUMMARY
    # ══════════════════════════════════════
    summary_left_w  = 95 * mm
    summary_right_w = col_w - summary_left_w
    summary_h       = 30 * mm

    draw_cell_border(margin_l, y - summary_h, summary_left_w, summary_h)
    draw_cell_border(margin_l + summary_left_w, y - summary_h, summary_right_w, summary_h)

    text(margin_l + 2*mm, y - 5*mm,  "Invoice Amount in Words", "Helvetica-Bold", 8)
    words = amount_in_words(total)
    # wrap long text
    if len(words) > 45:
        mid = words[:45].rfind(' ')
        text(margin_l + 2*mm, y - 10*mm, words[:mid],  "Helvetica", 7.5)
        text(margin_l + 2*mm, y - 14*mm, words[mid+1:], "Helvetica", 7.5)
    else:
        text(margin_l + 2*mm, y - 10*mm, words, "Helvetica", 7.5)

    # Right: amounts
    rx2  = margin_l + summary_left_w
    rw2  = summary_right_w

    # horizontal lines
    for i, offset in enumerate([8, 14, 20, 25]):
        c.setLineWidth(0.3)
        c.line(rx2, y - offset*mm, rx2 + rw2, y - offset*mm)

    # label col / value col
    lx = rx2 + 2*mm
    vx = rx2 + rw2 - 2*mm

    rows_amounts = [
        ("Amounts",    "",                    3),
        ("Sub Total",  f"Rs. {taxable:,.2f}", 7),
        (f"Tax (18%)", f"Rs. {gst_amount:,.2f}", 11),
        ("Total",      f"Rs. {total:,.2f}",   16),
        ("Received",   f"Rs. {received:,.2f}", 21),
        ("Balance",    f"Rs. {balance:,.2f}", 26),
    ]
    for label, value, offset in rows_amounts:
        bold = label in ("Amounts", "Total")
        fn = "Helvetica-Bold" if bold else "Helvetica"
        text(lx, y - offset*mm, label, fn, 8)
        if value:
            text(vx, y - offset*mm, value, fn, 8, align="right")

    y -= summary_h

    # ══════════════════════════════════════
    #  GST TABLE
    # ══════════════════════════════════════
    gst_row_h = 6 * mm
    gst_cols  = [30*mm, 35*mm, 20*mm, 20*mm, 25*mm, 25*mm]   # total ~155mm — adjust if needed
    gst_col_x = [margin_l]
    for cw in gst_cols[:-1]:
        gst_col_x.append(gst_col_x[-1] + cw)

    # header
    draw_cell_border(margin_l, y - gst_row_h, col_w, gst_row_h, fill=colors.HexColor('#f0f0f0'))
    gst_headers = ['HSN/SAC', 'Taxable Amount', 'IGST Rate', 'IGST Amt', 'Total Tax Amt', '']
    for i, (hdr, cx) in enumerate(zip(gst_headers, gst_col_x)):
        if i > 0:
            c.setLineWidth(0.5)
            c.line(cx, y - gst_row_h, cx, y)
        text(cx + gst_cols[i]/2, y - 4*mm, hdr, "Helvetica-Bold", 7, align="center")
    y -= gst_row_h

    # data row
    draw_cell_border(margin_l, y - gst_row_h, col_w, gst_row_h)
    gst_data = [HSN_SAC, f"Rs. {taxable:,.2f}", "18%", f"Rs. {gst_amount:,.2f}", f"Rs. {gst_amount:,.2f}", ""]
    for i, (val, cx) in enumerate(zip(gst_data, gst_col_x)):
        if i > 0:
            c.setLineWidth(0.5)
            c.line(cx, y - gst_row_h, cx, y)
        text(cx + gst_cols[i]/2, y - 4*mm, val, "Helvetica", 7.5, align="center")
    y -= gst_row_h

    # total row
    draw_cell_border(margin_l, y - gst_row_h, col_w, gst_row_h, fill=colors.HexColor('#f0f0f0'))
    for i, cx in enumerate(gst_col_x[1:], 1):
        c.setLineWidth(0.5)
        c.line(cx, y - gst_row_h, cx, y)
    text(gst_col_x[0] + gst_cols[0]/2, y - 4*mm, "Total", "Helvetica-Bold", 7.5, align="center")
    text(gst_col_x[1] + gst_cols[1]/2, y - 4*mm, f"Rs. {taxable:,.2f}", "Helvetica-Bold", 7.5, align="center")
    text(gst_col_x[3] + gst_cols[3]/2, y - 4*mm, f"Rs. {gst_amount:,.2f}", "Helvetica-Bold", 7.5, align="center")
    text(gst_col_x[4] + gst_cols[4]/2, y - 4*mm, f"Rs. {gst_amount:,.2f}", "Helvetica-Bold", 7.5, align="center")
    y -= gst_row_h

    # ══════════════════════════════════════
    #  FOOTER — Bank Details | Terms | Signatory
    # ══════════════════════════════════════
    footer_h = 35 * mm
    foot_col  = col_w / 3

    draw_cell_border(margin_l,               y - footer_h, foot_col, footer_h)
    draw_cell_border(margin_l + foot_col,    y - footer_h, foot_col, footer_h)
    draw_cell_border(margin_l + foot_col*2,  y - footer_h, foot_col, footer_h)

    # Bank Details
    bx = margin_l + 2*mm
    text(bx, y - 4*mm,  "Bank Details",          "Helvetica-Bold", 8)
    text(bx, y - 9*mm,  f"Name: {BANK_NAME}",    "Helvetica",      7)
    text(bx, y - 13*mm, f"Account No.: {BANK_ACCOUNT}", "Helvetica", 7)
    text(bx, y - 17*mm, f"IFSC code: {BANK_IFSC}", "Helvetica",    7)
    text(bx, y - 21*mm, f"Account holder: {BANK_HOLDER}", "Helvetica", 7)

    # Terms
    tx2 = margin_l + foot_col + 2*mm
    text(tx2, y - 4*mm, "Terms and conditions", "Helvetica-Bold", 8)
    text(tx2, y - 9*mm, TERMS, "Helvetica", 7.5)

    # Signatory
    sx = margin_l + foot_col*2 + 2*mm
    text(sx, y - 4*mm,  f"For: {COMPANY_NAME[:25]}", "Helvetica-Bold", 7)
    text(sx, y - 25*mm, "Authorized Signatory",       "Helvetica-Bold", 7.5)

    y -= footer_h

    # ══════════════════════════════════════
    #  Save
    # ══════════════════════════════════════
    c.save()
    buffer.seek(0)

    filename = f"Invoice_{inv_number}.pdf"
    return FileResponse(buffer, as_attachment=True, filename=filename)

# ============================================================
# ✅ 2. Dashboard order detail view — approve/revoke logic
#    Yeh function apne dashboard views.py mein update karo
# ============================================================

# Dashboard views.py mein (dashboard/views.py ya jahan bhi hai)
from store.models import Order  # apna import path adjust karo

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
            messages.success(request, f'Invoice approved! Customer ab download kar sakta hai.')

        elif action == 'revoke_invoice':
            order.invoice_approved = False
            order.save()
            messages.warning(request, f'Invoice approval revoke kar diya gaya.')

        return redirect('dashboard_order_detail', order_id=order.order_id)

    return render(request, 'dashboard/order_detail.html', {'order': order})