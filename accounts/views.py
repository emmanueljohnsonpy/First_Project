import random
import time
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegisterationForm, UserForm
from .models import Account, UserProfile
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from django.utils.encoding import force_bytes
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
import requests
from django.utils.http import urlsafe_base64_decode
from carts.models import Cart, CartItem
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import login as auth_login, get_backends
from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from django.contrib import messages
from carts.views import _cart_id
import requests
from django.db.models import ObjectDoesNotExist
from store.models import Product
from accounts.models import Account
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages

from django.contrib.sessions.models import Session
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.sessions.models import Session
import requests
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.sessions.models import Session
from carts.models import Cart, CartItem
import requests
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.shortcuts import render, redirect
from django.contrib import messages
from carts.models import Cart, CartItem
from orders.models import Order
from django.shortcuts import render, redirect
from .models import Address
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from orders.models import Wallet, WalletTransaction
from orders.models import ReferralOffer


OTP_EXPIRY_TIME = 60  # seconds

def generate_otp():
    return str(random.randint(1000, 9999))
from .utils import generate_referral_code
def send_otp_email(to_email, otp):
    subject = 'Your OTP Code'
    message = f'Your OTP code is {otp}. Please enter this code to verify your email.'
    from_email = settings.EMAIL_HOST_USER
    send_email = EmailMessage(subject, message, from_email, [to_email])
    send_email.send()

def register(request):
    if request.method == 'POST':
        form = RegisterationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, username=username, password=password)
            user.phone_number = phone_number
            user.is_active = False  # Set inactive until verified
            user.save()

            # Create referral offer
            referral_code = generate_referral_code()
            ReferralOffer.objects.create(
                user=user,
                code=referral_code,
                reward_amount=100,
                is_active=True,
                usage_limit=1,
                # No start_date, end_date, or description needed
            )

            # Generate OTP
            otp = generate_otp()
            request.session['otp'] = otp
            request.session['otp_email'] = email
            request.session['otp_generated_at'] = time.time()

            # Send OTP email
            current_site = get_current_site(request)
            mail_subject = 'Your OTP Code'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'otp': otp,
            })
            send_email = EmailMessage(mail_subject, message, from_email=settings.EMAIL_HOST_USER, to=[email])
            send_email.send()

            return redirect('verify_otp')
    else:
        form = RegisterationForm()
    context = {
        'form': form,
    }
    return render(request, 'accounts/register.html', context)
OTP_EXPIRY_TIME = 300  # Set OTP expiry time in seconds

def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        email = request.session.get('otp_email')
        otp_generated_at = request.session.get('otp_generated_at')

        if not all([entered_otp, stored_otp, email, otp_generated_at]):
            messages.error(request, 'Missing OTP or session data. Please try again.')
            return redirect('register')

        if time.time() - otp_generated_at > OTP_EXPIRY_TIME:
            messages.error(request, 'OTP has expired. Please request a new one.')
            return redirect('register')

        if entered_otp == stored_otp:
            try:
                user = Account.objects.get(email=email)
                user.is_active = True
                user.save()

                # Set the backend attribute manually
                backend = get_backends()[0]  # Assuming you want to use the first backend
                user.backend = f'{backend.__module__}.{backend.__class__.__name__}'
                
                # Log the user in
                auth_login(request, user)

                return redirect('home')
            except Account.DoesNotExist:
                messages.error(request, 'Account with this email does not exist.')
                return redirect('register')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')
            return redirect('verify_otp')

    return render(request, 'accounts/verify_otp.html')


def resend_otp(request):
    email = request.session.get('otp_email')
    if email:
        otp = generate_otp()
        request.session['otp'] = otp
        request.session['otp_generated_at'] = time.time()
        
        send_otp_email(email, otp)
        messages.success(request, 'New OTP has been sent to your email.')
    else:
        messages.error(request, 'Could not resend OTP. Please try again.')
    return redirect('verify_otp')




def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if the email exists in the database and if the user is inactive
        try:
            user = Account.objects.get(email=email)
            if not user.is_blocked:
                messages.warning(request, 'Your account is blocked. Please contact support.')
                return redirect('login')
        except User.DoesNotExist:
            pass  # If the user doesn't exist, proceed with the standard authentication flow

        user = authenticate(request, email=email, password=password)
        if user is not None:
            if not user.is_blocked:
                messages.warning(request, 'Your account is blocked. Please contact support.')
                return redirect('login')

            # Ensure the user is not an admin
            if user.is_staff or user.is_superuser:
                messages.error(request, 'Admin accounts cannot log in here.')
                return redirect('login')

            # Clear any existing admin session
            if 'is_admin' in request.session:
                del request.session['is_admin']

            if 'admin_session_key' in request.session:
                session = Session.objects.get(pk=request.session['admin_session_key'])
                session.delete()

            # Handle cart logic
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)

                    # Getting the product variations by cart id
                    product_variation = []
                    for item in cart_item:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get the cart items from the user to access his product variations    
                    cart_item = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id = []
                    for item in cart_item:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id.append(item.id)

                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            cart_item = CartItem.objects.filter(cart=cart)
                            for item in cart_item:
                                item.user = user
                                item.save()
            except Cart.DoesNotExist:
                cart = Cart.objects.create(cart_id=_cart_id(request))
                cart.save()

            auth_login(request, user)
            request.session['user_session_key'] = request.session.session_key
        

            url = request.META.get('HTTP_REFERER')
            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    if 'admin' in nextPage and user.is_staff:
                        return redirect(nextPage)
                    else:
                        return redirect('home')
            except Exception as e:
                print(f"Error parsing URL: {e}")
                return redirect('home')
        else:
            messages.error(request, 'Invalid login credentials')
            return redirect('login')

    return render(request, 'accounts/login.html')





@login_required(login_url='login')
def logout(request): 
    auth.logout(request)
    messages.success(request, 'You are logged out.')
    return redirect('login')

def user_required(user):
    return not user.is_staff and not user.is_superuser
user_login_required = user_passes_test(user_required, login_url=reverse_lazy('login'))

@user_login_required
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id)
    orders_count = orders.count()


    context = {
        'orders_count': orders_count,
    
    }
    return render(request, 'accounts/dashboard.html', context) 

def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email=email)
            
            # Reset password email
            current_site = get_current_site(request)
            mail_subject = 'Reset Your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, from_email=settings.EMAIL_HOST_USER, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address.')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist!')
            return redirect('forgotPassword')
    return render(request, 'accounts/forgotPassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your password')
        return redirect('resetPassword')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('login')

def resetPassword(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Passwords do not match!')
            return redirect('resetPassword')
    else:
        return render(request, 'accounts/resetPassword.html')
    


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been activated. You can now log in.')
        return redirect('login')
    else:
        messages.error(request, 'Activation link is invalid or has expired.')
        return redirect('login')

def returntolog(request):
    return redirect('login')


# @login_required(login_url='login')
# def logout(request):
#     user = request.user
#     user.is_active = False
#     user.save()
#     auth_logout(request)
#     messages.success(request, 'You are logged out.')
#     return redirect('login')


@login_required
@user_login_required
def edit_profile(request):
    if request.method == 'POST':
        # Get the current user
        user = request.user
        
        # Update user fields
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('phone_number')
        
        # Validate and save the data
        if first_name and last_name and phone_number:
            user.first_name = first_name
            user.last_name = last_name
            user.phone_number = phone_number
            user.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('ac_details')  # Redirect to the profile page or another appropriate page
        else:
            messages.error(request, 'All fields are required.')

    return HttpResponse(status=400)  

@login_required(login_url='login')
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']

        user = Account.objects.get(username__exact=request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Password updated successfully.')
                return redirect('change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match!')
            return redirect('change_password')
    return render(request, 'accounts/change_password.html')

@login_required
@user_login_required
def address(request):
    user_addresses = Address.objects.filter(user=request.user).order_by('-id')  # Fetch all addresses and order by most recent
    if request.method == "POST":
        # Retrieve form data
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        address_line2 = request.POST.get('address_line2', '')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        # Create and save the address to the database
        Address.objects.create(
            user=request.user,
            full_name=full_name,
            address=address,
            address_line2=address_line2,
            city=city,
            state=state,
            pincode=pincode,
            phone=phone,
            email=email
        )

        # Success message and redirect
        messages.success(request, 'Address added successfully!')
        return redirect('address')  # Replace with the name of the view you want to redirect to
    
    return render(request, 'accounts/address.html', {'user_addresses': user_addresses})

@login_required
@user_login_required
def edit_address(request, id):
    address = get_object_or_404(Address, id=id)
    
    if request.method == 'POST':
        address.full_name = request.POST.get('full_name')
        address.address = request.POST.get('address')
        address.address_line2 = request.POST.get('address_line2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.pincode = request.POST.get('pincode')
        address.phone = request.POST.get('phone')
        address.email = request.POST.get('email')
        address.save()

        messages.success(request, 'Address updated successfully!')
        return redirect('address')

    return render(request, 'accounts/edit_address.html', {'address': address})


def delete_address_profile(request, id):
    address = get_object_or_404(Address, id=id, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        return redirect('address')  # Replace 'address' with your actual view name
    
    return redirect('address')  

def ac_details(request):
    return render(request, 'accounts/ac_details.html')


from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from orders.models import Order, Wallet, WalletTransaction

@login_required(login_url='login')
@user_login_required
def my_orders(request):
    # Fetch orders for the logged-in user and order them by creation date in descending order
    orders = Order.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        if order_id:
            order = get_object_or_404(Order, id=order_id, user=request.user)

            # Restocking logic for canceled orders
            ordered_items = OrderedItems.objects.filter(order_number=order.order_number)

            if order.status in ['Pending', 'Confirmed', 'Processing']:
                # Restock items before canceling the order
                for item in ordered_items:
                    if item.size == 'Size 3':
                        item.product.stock_small += item.quantity
                    elif item.size == 'Size 4':
                        item.product.stock_medium += item.quantity
                    elif item.size == 'Size 5':
                        item.product.stock_large += item.quantity
                    item.product.save()

                # Update order status to 'Cancelled'
                order.status = 'Cancelled'
                order.save()
                
                # Update or create wallet
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.update_balance('credit', Decimal(str(order.grand_total)))
                
                # Create a new wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=Decimal(str(order.grand_total)),
                    transaction_type='credit',
                    description=f'Refund for cancelled order #{order.id}'
                )
                
                messages.success(request, 'Your order has been cancelled and the amount has been added to your wallet.')
            elif order.status == 'Delivered':
                # order.status = 'Return Pending'
                order.status = 'Return Request'
                order.save()
                # Update or create wallet
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.update_balance('credit', Decimal(str(order.grand_total)))
                
                # Create a new wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=Decimal(str(order.grand_total)),
                    transaction_type='credit',
                    description=f'Refund for returned order #{order.id}'
                )
                messages.success(request, 'Your return request has been submitted, and money has been added to your balance.')
            elif order.status == 'Return Pending':
                order.status = 'Delivered'
                order.save()
                messages.success(request, 'Your return request has been submitted, and money has been added to your balance.')
            
            return redirect('my_orders')  # Redirect to avoid resubmission on refresh
    
    return render(request, 'accounts/my_orders.html', {'orders': orders})





# if order.status == 'Pending' or order.status == 'Confirmed' or order.status =='Processing':


from decimal import Decimal
from django.shortcuts import render
from orders.models import Wallet, WalletTransaction
@user_login_required
def wallet(request):
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    wallet_transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-date')

    referral_offer = ReferralOffer.objects.filter(user=request.user, is_active=True).first()
    referral_code = referral_offer.code if referral_offer else "No active referral offer"

    context = {
        'wallet': wallet,
        'wallet_transactions': wallet_transactions,
        'referral_code': referral_code,
    }
    return render(request, 'accounts/wallet.html', context)

from django.http import JsonResponse
@login_required
def apply_referral_code(request):
    if request.method == 'POST':
        friend_code = request.POST.get('friend_code')
        user = request.user
        
        # Check if referral code is valid
        referral_offer = ReferralOffer.objects.filter(code=friend_code, is_active=True).first()
        if referral_offer:
            # Update wallet balance
            wallet, created = Wallet.objects.get_or_create(user=user)
            wallet.update_balance(transaction_type='credit', amount=referral_offer.reward_amount)
            
            # Record the transaction
            WalletTransaction.objects.create(
                wallet=wallet,
                amount=referral_offer.reward_amount,
                transaction_type='credit',
                description=f"Referral reward for code {friend_code}"
            )

            # Optionally, deactivate the referral code if it has a usage limit
            if referral_offer.usage_limit:
                referral_offer.usage_limit -= 1
                if referral_offer.usage_limit <= 0:
                    referral_offer.is_active = False
                referral_offer.save()

            return JsonResponse({'success': True, 'message': 'Referral code applied successfully!'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid referral code.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



from accounts.models import Address
from django.shortcuts import get_object_or_404, render
from orders.models import OrderedItems, Order
from django.db.models import Sum, F
@user_login_required
def order_detail_view_user(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    STATUS_CHOICES = Order.STATUS_CHOICES
    
    ordered_items = OrderedItems.objects.filter(order_number=order.order_number)
    
    aggregated_items = (
        ordered_items
        .select_related('product')
        .values('product__image1','product__product_name', 'size', 'product__id', 'unit_price')
        .annotate(
            total_quantity=Sum('quantity'),
            total_price=Sum(F('unit_price') * F('quantity'))
        )
    )
    
    # Debug print
    for item in aggregated_items:
        print(item)  # Print the aggregated items to debug
    
    order_address = {
        'address_line1': order.address_line1,
        'address_line2': order.address_line2,
        'city': order.city,
        'state': order.state,
        'country': order.country,
        'pincode': order.pincode,
    }

    return render(request, 'accounts/order_detail_view_user.html', {
        'order': order,
        'status_choices': STATUS_CHOICES,
        'aggregated_items': aggregated_items,
        'order_address': order_address
    })

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from django.db.models import Sum, F
from django.shortcuts import get_object_or_404

def generate_pdf(request, order_id):
    # Fetch the order and related data
    order = get_object_or_404(Order, id=order_id)
    ordered_items = OrderedItems.objects.filter(order_number=order.order_number)
    checked_address = Address.objects.filter(user=request.user, checked=True).first()

    aggregated_items = (
        ordered_items
        .select_related('product')
        .values('product__image1', 'product__product_name', 'size', 'product__id', 'unit_price', 'shipping_fee')
        .annotate(
            total_quantity=Sum('quantity'),
            total_price=Sum(F('unit_price') * F('quantity'))
        )
    )
    print(f"Order Number: {order.order_number}")
    # Render the template with the context data
    html_string = render_to_string('accounts/invoice_template.html', {
        'order': order,
        'aggregated_items': aggregated_items,
        'checked_address': checked_address
    })

    # Convert HTML to PDF
    pdf_file = HTML(string=html_string).write_pdf()

    # Create the response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="order_{order_id}.pdf"'
    return response
