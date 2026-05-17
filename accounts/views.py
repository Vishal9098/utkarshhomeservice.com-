from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from store.models import UserProfile, Order


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone', '')

        if password != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'accounts/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists!')
            return render(request, 'accounts/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered!')
            return render(request, 'accounts/register.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(user=user, phone=phone)
        login(request, user)
        messages.success(request, f'Welcome {username}! Your account has been created successfully.')
        return redirect('home')

    return render(request, 'accounts/register.html')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # Email se user dhundo
        user_obj = User.objects.filter(email=email).first()
        if user_obj:
            user = authenticate(request, username=user_obj.username, password=password)
        else:
            user = None

        if user:
            login(request, user)
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid email or password. Please try again.')

    return render(request, 'accounts/login.html')


def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        # FIX: .get() ki jagah .filter().first() use kiya
        # Taaki duplicate users hone par bhi error na aaye
        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'accounts/forgot_password.html')

        try:
            # Generate random token
            token = get_random_string(32)
            # Token profile mein save karo
            profile_obj, _ = UserProfile.objects.get_or_create(user=user)
            profile_obj.reset_token = token
            profile_obj.save()

            reset_link = request.build_absolute_uri(f'/accounts/reset-password/{token}/')

            send_mail(
                subject='Password Reset - Utkarsh Cleaning',
                message=f'Hello {user.username},\n\nClick the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, please ignore this email.\n\nUtkarsh Cleaning Team',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, 'Password reset link has been sent to your email.')
            return redirect('login')

        except Exception as e:
            messages.error(request, 'Something went wrong. Please try again.')

    return render(request, 'accounts/forgot_password.html')


def reset_password(request, token):
    try:
        profile_obj = UserProfile.objects.get(reset_token=token)
        user = profile_obj.user
    except UserProfile.DoesNotExist:
        messages.error(request, 'Invalid or expired password reset link.')
        return redirect('login')

    if request.method == 'POST':
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        if password != password2:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'accounts/reset_password.html', {'token': token})

        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return render(request, 'accounts/reset_password.html', {'token': token})

        user.set_password(password)
        user.save()
        profile_obj.reset_token = ''
        profile_obj.save()
        messages.success(request, 'Password reset successfully! Please login with your new password.')
        return redirect('login')

    return render(request, 'accounts/reset_password.html', {'token': token})


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
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'profile': profile_obj, 'orders': orders})