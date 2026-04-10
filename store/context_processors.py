from .models import Cart, CartItem, Category

def cart_count(request):
    count = 0
    categories_global = Category.objects.filter(is_active=True)
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            session_key = request.session.session_key
            cart = Cart.objects.filter(session_key=session_key).first() if session_key else None
        if cart:
            count = cart.items.count()
    except:
        pass
    return {'cart_count': count, 'categories_global': categories_global}
