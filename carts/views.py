from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product
from .models import Cart, CartItem
from django.contrib.auth.decorators import login_required
from accounts.models import Address
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from .models import Product, Cart, CartItem
from orders.models import Coupon
from datetime import date

def user_required(user):
    return not user.is_staff and not user.is_superuser

user_login_required = user_passes_test(user_required, login_url=reverse_lazy('login'))

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

# def add_cart(request, product_id):
#     current_user = request.user
#     product = get_object_or_404(Product, id=product_id)  # Get the product
#     selected_size = request.POST.get('size')  # Get the selected size from the request
#     unit_price = product.price
#     # Function to handle cart item quantity increment
#     def handle_cart_item_quantity(cart_item, quantity):
#         if cart_item.quantity + quantity <= 10:
#             cart_item.quantity += quantity
#             cart_item.save()

#     # If the user is authenticated
#     if current_user.is_authenticated:
#         is_cart_item_exists = CartItem.objects.filter(product=product, user=current_user, size=selected_size).exists()
#         if is_cart_item_exists:
#             cart_item = CartItem.objects.filter(product=product, user=current_user, size=selected_size).first()
#             handle_cart_item_quantity(cart_item, 1)
#         else:
#             CartItem.objects.create(product=product, quantity=1, user=current_user, size=selected_size, unit_price=unit_price)
#     else:  # If the user is not authenticated
#         try:
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#         except Cart.DoesNotExist:
#             cart = Cart.objects.create(cart_id=_cart_id(request))
#         cart.save()

#         is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart, size=selected_size).exists()
#         if is_cart_item_exists:
#             cart_item = CartItem.objects.filter(product=product, cart=cart, size=selected_size).first()
#             handle_cart_item_quantity(cart_item, 1)
#         else:
#             CartItem.objects.create(product=product, quantity=1, cart=cart, size=selected_size)

#     return redirect('cart')
def add_cart(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    selected_size = request.POST.get('size')
    unit_price = product.price
    
    # Determine available stock based on the selected size
    if selected_size == 'Size 3':
        available_stock = product.stock_small
    elif selected_size == 'Size 4':
        available_stock = product.stock_medium
    elif selected_size == 'Size 5':
        available_stock = product.stock_large
    else:
        available_stock = 0

    # Function to handle cart item quantity increment
    def handle_cart_item_quantity(cart_item, quantity):
        if cart_item.quantity + quantity <= available_stock and cart_item.quantity + quantity <= 10:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            messages.error(request, f"Cannot add more than {available_stock} items in stock.")

    # If the user is authenticated
    if current_user.is_authenticated:
        cart_items = CartItem.objects.filter(product=product, user=current_user, size=selected_size)
        total_quantity_in_cart = sum(item.quantity for item in cart_items)

        if total_quantity_in_cart >= available_stock:
            messages.error(request, f"Sorry, only {available_stock} items left in {selected_size}.")
        else:
            if cart_items.exists():
                cart_item = cart_items.first()
                handle_cart_item_quantity(cart_item, 1)
            else:
                CartItem.objects.create(product=product, quantity=1, user=current_user, size=selected_size, unit_price=unit_price)
    else:
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

        cart_items = CartItem.objects.filter(product=product, cart=cart, size=selected_size)
        total_quantity_in_cart = sum(item.quantity for item in cart_items)

        if total_quantity_in_cart >= available_stock:
            messages.error(request, f"Sorry, only {available_stock} items left in {selected_size}.")
        else:
            if cart_items.exists():
                cart_item = cart_items.first()
                handle_cart_item_quantity(cart_item, 1)
            else:
                CartItem.objects.create(product=product, quantity=1, cart=cart, size=selected_size)

    return redirect('cart')


# def increment_cart_item(request, product_id):
#     current_user = request.user
#     product = get_object_or_404(Product, id=product_id)
#     selected_size = request.POST.get('size')  # Get the selected size from the request

#     # Check stock based on selected size
#     if selected_size == 'Size 3':
#         available_stock = product.stock_small
#     elif selected_size == 'Size 4':
#         available_stock = product.stock_medium
#     elif selected_size == 'Size 5':
#         available_stock = product.stock_large
#     else:
#         available_stock = 0

#     if available_stock <= 0:
#         messages.error(request, f'Sorry, {selected_size} size is out of stock.')
#         return redirect('cart')

#     if current_user.is_authenticated:
#         try:
#             cart_item = CartItem.objects.get(product=product, user=current_user, size=selected_size)
#             if cart_item.quantity < 10:  # Assuming 10 is the max quantity
#                 if cart_item.quantity < available_stock:
#                     cart_item.quantity += 1
#                     if selected_size == 'Size 3':
#                         product.stock_small -= 1
#                     elif selected_size == 'Size 4':
#                         product.stock_medium -= 1
#                     elif selected_size == 'Size 5':
#                         product.stock_large -= 1
#                     cart_item.save()
#                 else:
#                     messages.error(request, f'Sorry, only {available_stock} items left in {selected_size}.')
#         except CartItem.DoesNotExist:
#             pass  # Handle the case where the item does not exist

#     else:
#         try:
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_item = CartItem.objects.get(product=product, cart=cart, size=selected_size)
#             if cart_item.quantity < 10:  # Assuming 10 is the max quantity
#                 if cart_item.quantity < available_stock:
#                     cart_item.quantity += 1
#                     if selected_size == 'Size 3':
#                         product.stock_small -= 1
#                     elif selected_size == 'Size 4':
#                         product.stock_medium -= 1
#                     elif selected_size == 'Size 5':
#                         product.stock_large -= 1
#                     cart_item.save()
#                 else:
#                     messages.error(request, f'Sorry, only {available_stock} items left in {selected_size}.')
#         except (CartItem.DoesNotExist, Cart.DoesNotExist):
#             pass  # Handle the case where the item does not exist or the cart does not exist

#     return redirect('cart')



# def decrement_cart_item(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     selected_size = request.GET.get('size')  # Get the size from the request if applicable

#     try:
#         if request.user.is_authenticated:
#             # Get the cart item for the authenticated user with the same size
#             cart_item = CartItem.objects.get(product=product, user=request.user, size=selected_size)
#         else:
#             # Get the cart item for the session cart with the same size
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_item = CartItem.objects.get(product=product, cart=cart, size=selected_size)

#         # Decrement quantity only if it's greater than 1
#         if cart_item.quantity > 1:
#             cart_item.quantity -= 1
#             cart_item.save()
#         # Else, do nothing (i.e., do not decrement below 1)
#     except CartItem.DoesNotExist:
#         pass  # Just ignore if cart item does not exist

#     return redirect('cart')
from django.http import JsonResponse
def increment_cart_item(request, product_id):
    current_user = request.user
    product = get_object_or_404(Product, id=product_id)
    selected_size = request.POST.get('size')

    # Check stock based on selected size
    available_stock = {
        'Size 3': product.stock_small,
        'Size 4': product.stock_medium,
        'Size 5': product.stock_large
    }.get(selected_size, 0)

    if available_stock <= 0:
        return JsonResponse({'error': f'Sorry, {selected_size} size is out of stock.'})

    if current_user.is_authenticated:
        try:
            cart_item = CartItem.objects.get(product=product, user=current_user, size=selected_size)
            if cart_item.quantity < 10:
                if cart_item.quantity < available_stock:
                    cart_item.quantity += 1
                    if selected_size == 'Size 3':
                        product.stock_small -= 1
                    elif selected_size == 'Size 4':
                        product.stock_medium -= 1
                    elif selected_size == 'Size 5':
                        product.stock_large -= 1
                    cart_item.save()
                    return JsonResponse({'success': True, 'new_quantity': cart_item.quantity, 'new_subtotal': int(cart_item.quantity * product.price) })
                else:
                    return JsonResponse({'error': f'Sorry, only {available_stock} items left in {selected_size}.'})
            else:
                return JsonResponse({'error': 'Sorry, you can only order 10 items.'})
        except CartItem.DoesNotExist:
            return JsonResponse({'error': 'Cart item does not exist.'})

    return JsonResponse({'error': 'User not authenticated.'})

def decrement_cart_item(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    selected_size = request.GET.get('size')

    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, size=selected_size)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, size=selected_size)

        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            return JsonResponse({'success': True, 'new_quantity': cart_item.quantity, 'new_subtotal': int(cart_item.quantity * product.price)})
        else:
            return JsonResponse({'error': 'This item has reached its minimum quantity.'

})
    except CartItem.DoesNotExist:
        return JsonResponse({'error': 'Cart item does not exist.'})

    return JsonResponse({'error': 'Cannot decrement item.'})



def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    size = request.GET.get('size')  # Get the size from the request if needed
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id, size=size)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id, size=size)
        
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        # If quantity is 1, do nothing instead of deleting or decreasing
    except CartItem.DoesNotExist:
        pass  # Just ignore if cart item does not exist

    return redirect('cart')



def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    except CartItem.DoesNotExist:
        pass  # Just ignore if cart item does not exist
    return redirect('cart')

@user_login_required
def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax_rate = 2  # Example tax rate; you can make this configurable
        tax = 0
        grand_total = 0
        available_coupons = Coupon.objects.filter(status='active', expiry_date__gte=date.today(), quantity__gt=0)

        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True).order_by('id')  # Order by ID
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')  # Order by ID

        for cart_item in cart_items:
            # Determine available stock based on the selected size
            if cart_item.size == 'Size 3':
                available_stock = cart_item.product.stock_small
            elif cart_item.size == 'Size 4':
                available_stock = cart_item.product.stock_medium
            elif cart_item.size == 'Size 5':
                available_stock = cart_item.product.stock_large
            else:
                available_stock = 0
            
            # Adjust quantity if it exceeds available stock
            if cart_item.quantity > available_stock:
                cart_item.quantity = available_stock  # Decrease quantity to match available stock
                cart_item.save()  # Save the updated quantity
                messages.info(request, f"Quantity for {cart_item.product.product_name} has been adjusted to available stock ({available_stock}).")

            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (tax_rate * total) / 100
        grand_total = total + tax

    except ObjectDoesNotExist:
        cart_items = []  # Fallback to empty list if cart or cart items do not exist

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'available_coupons': available_coupons,
    }

    return render(request, 'store/cart.html', context)

# @user_login_required
# def cart(request, total=0, quantity=0, cart_items=None):
#     try:
#         tax_rate = 2  # Example tax rate; you can make this configurable
#         tax = 0
#         grand_total = 0
#         available_coupons = Coupon.objects.filter(status='active', expiry_date__gte=date.today(), quantity__gt=0)

        
#         if request.user.is_authenticated:
#             cart_items = CartItem.objects.filter(user=request.user, is_active=True).order_by('id')  # Order by ID
#         else:
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_items = CartItem.objects.filter(cart=cart, is_active=True).order_by('id')  # Order by ID

#         for cart_item in cart_items:
#             total += (cart_item.product.price * cart_item.quantity)
#             quantity += cart_item.quantity

#         tax = (tax_rate * total) / 100
#         grand_total = total + tax

#     except ObjectDoesNotExist:
#         cart_items = []  # Fallback to empty list if cart or cart items do not exist

#     context = {
#         'total': total,
#         'quantity': quantity,
#         'cart_items': cart_items,
#         'tax': tax,
#         'grand_total': grand_total,
#         'available_coupons': available_coupons,
#     }

#     return render(request, 'store/cart.html', context)
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from .models import CheckoutDetails, CartItem, Cart  # Adjust your imports
from accounts.models import Address
import razorpay
@login_required(login_url='login')
@user_login_required
def checkout(request):
    if request.method == 'GET':
        try:
            total = 0
            quantity = 0
            tax = 0
            shipping_fee = 50
            grand_total = 0
            cart_items = None
            user_addresses = []
            razorpay_order_id = None

            if request.user.is_authenticated:
                cart_items = CartItem.objects.filter(user=request.user, is_active=True)
                user_addresses = Address.objects.filter(user=request.user)
            else:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            
            # Validate stock availability
            insufficient_stock_items = []
            for cart_item in cart_items:
                if cart_item.size == 'Size 3' and cart_item.product.stock_small < cart_item.quantity:
                    insufficient_stock_items.append((cart_item.product.product_name, 'Size 3'))
                elif cart_item.size == 'Size 4' and cart_item.product.stock_medium < cart_item.quantity:
                    insufficient_stock_items.append((cart_item.product.product_name, 'Size 4'))
                elif cart_item.size == 'Size 5' and cart_item.product.stock_large < cart_item.quantity:
                    insufficient_stock_items.append((cart_item.product.product_name, 'Size 5'))

            if insufficient_stock_items:
                messages.error(request, 'Insufficient stock for the following items: ' + ', '.join(
                    [f"{name} ({size})" for name, size in insufficient_stock_items]
                ))
                return redirect('cart')  # Redirect to the cart page or appropriate page


            for cart_item in cart_items:
                total += (cart_item.product.price * cart_item.quantity)
                quantity += cart_item.quantity

            tax = (2 * total) / 100
            grand_total = total + tax + shipping_fee

            # Initialize Razorpay client
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

            # Create Razorpay order
            order_data = {
                'amount': int(grand_total * 100),  # Amount in paise
                'currency': 'INR',
                'receipt': 'order_rcptid_11',
                'payment_capture': '1'  # Automatic capture
            }
            razorpay_order = client.order.create(data=order_data)
            razorpay_order_id = razorpay_order['id']

            # Save checkout details in the database
            checkout_details = CheckoutDetails.objects.create(
                user=request.user,
                name=request.user.get_full_name(),
                email=request.user.email,
                total_price=total,
                tax=tax,
                grand_total=grand_total,
                razorpay_order_id=razorpay_order_id,  # Save the Razorpay order ID
                razorpay_key_id=settings.RAZORPAY_KEY_ID,  # Save the Razorpay Key ID
                before_price=grand_total,
                shipping_fee=50
            )
            
            context = {
                'checkout_details': checkout_details,
                'razorpay_order_id': razorpay_order_id,  # Pass the Razorpay order ID to the template
                'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID,  # Pass the Razorpay Key ID to the template
                'total': total,
                'quantity': quantity,
                'cart_items': cart_items,
                'tax': tax,
                'shipping_fee': shipping_fee,
                'grand_total': grand_total,
                'user_addresses': user_addresses
            }

            return render(request, 'store/checkout.html', context)

        except ObjectDoesNotExist:
            return JsonResponse({'success': False, 'message': "Cart or cart items not found."})
        except Exception as e:
            # Handle unexpected exceptions
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': "Invalid request method."})

