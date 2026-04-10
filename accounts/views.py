from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from store.models import UserProfile, Order

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone', '')
        if password != password2:
            messages.error(request, 'Passwords match nahi kar rahe!')
            return render(request, 'accounts/register.html')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exist karta hai!')
            return render(request, 'accounts/register.html')
        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, phone=phone)
        login(request, user)
        messages.success(request, f'Welcome {username}! Account successfully create ho gaya.')
        return redirect('home')
    return render(request, 'accounts/register.html')

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        messages.error(request, 'Invalid username ya password!')
    return render(request, 'accounts/login.html')

def user_logout(request):
    logout(request)
    messages.success(request, 'Successfully logout ho gaye.')
    return redirect('home')

@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        profile_obj.phone = request.POST.get('phone', '')
        profile_obj.address = request.POST.get('address', '')
        profile_obj.city = request.POST.get('city', '')
        profile_obj.pincode = request.POST.get('pincode', '')
        if 'profile_image' in request.FILES:
            profile_obj.profile_image = request.FILES['profile_image']
        profile_obj.save()
        messages.success(request, 'Profile update ho gaya!')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'profile': profile_obj, 'orders': orders})
