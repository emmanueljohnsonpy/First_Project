from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Address
from .models import Order, OrderItem, Payment
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from carts.models import CartItem, Cart
import datetime
from store.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Order, OrderItem, Payment
from django.utils import timezone
from .utils import get_cart_items
from .models import Coupon
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy
from collections import defaultdict
def user_required(user):
    return not user.is_staff and not user.is_superuser

user_login_required = user_passes_test(user_required, login_url=reverse_lazy('login'))

def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered=False, order_number=body['orderID'])

    # Store transaction details inside Payment model
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method = body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],
    )
    payment.save()

    order.payment = payment
    order.is_ordered = True
    order.save()

    # Move the cart items to Order Product table
    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = request.user.id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        cart_item = CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct = OrderProduct.objects.get(id=orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()


        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()

    # Send order recieved email to customer
    mail_subject = 'Thank you for your order!'
    message = render_to_string('orders/order_recieved_email.html', {
        'user': request.user,
        'order': order,
    })
    to_email = request.user.email
    send_email = EmailMessage(mail_subject, message, to=[to_email])
    send_email.send()

    # Send order number and transaction id back to sendData method via JsonResponse
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
    }
    return JsonResponse(data)


def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.get(payment_id=transID)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': payment.payment_id,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    except (Payment.DoesNotExist, Order.DoesNotExist):
        return redirect('home')

@login_required
@user_login_required
def orders_address(request):
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
        Address.objects.filter(user=request.user).update(checked=False)
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
            email=email,    
            checked=True

        )

        # Success message and redirect
        messages.success(request, 'Address added successfully!')
        return redirect('checkout')  # Replace with the name of the view you want to redirect to
    
    return render(request, 'store/checkout.html', {'user_addresses': user_addresses})




@login_required
def update_address(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        address = get_object_or_404(Address, id=address_id, user=request.user)
        address.full_name = request.POST.get('full_name')
        address.address = request.POST.get('address')
        address.address_line2 = request.POST.get('address_line2')
        address.city = request.POST.get('city')
        address.state = request.POST.get('state')
        address.pincode = request.POST.get('pincode')
        address.phone = request.POST.get('phone')
        address.email = request.POST.get('email')
        address.save()

        # Optionally, add a success message
        messages.success(request, 'Address updated successfully.')

    return redirect('checkout')  # Redirect to checkout page or wherever you need




def delete_address(request, id):
    # Get the address object or return a 404 error if not found
    address = get_object_or_404(Address, id=id)
    
    # Check if the request method is POST
    if request.method == 'POST':
        # Delete the address
        address.delete()
        
        # Add a success message
        messages.success(request, 'Address deleted successfully.')
        
        # Redirect to a desired page, for example, the address list page
        return redirect('checkout')  # Change 'address_list' to your actual view name

    # If the request method is not POST, redirect back to the address list
    return redirect('checkout')

def calculate_tax(total):
    # Implement tax calculation logic
    return total * 0.1  # Example tax rate of 10%


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from carts.models import CartItem, Cart
from carts.views import _cart_id
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
import random
from carts.models import CheckoutDetails
from decimal import Decimal
from .models import Wallet, WalletTransaction
from django.db import transaction
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import razorpay
from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
from accounts.models import Address
from .models import OrderedItems
@csrf_exempt
@login_required(login_url='login')
def place_order(request):
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        if coupon_id == '':
            coupon_id = None
        cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        total = sum(item.sub_total() for item in cart_items)
        tax = (2 * total) / 100
        shipping_fee = 50
        grand_total = total + tax + shipping_fee
        payment_method = request.POST.get('payment_method')
        address = Address.objects.filter(user=request.user, checked=True).first()

        # Check stock availability
        stock_check_passed = True
        for item in cart_items:
            product = item.product
            if item.size == 'Size 3' and item.quantity > product.stock_small:
                messages.error(request, f'Insufficient stock for {product.product_name} (Size 3).')
                stock_check_passed = False
                break
            elif item.size == 'Size 4' and item.quantity > product.stock_medium:
                messages.error(request, f'Insufficient stock for {product.product_name} (Size 4).')
                stock_check_passed = False
                break
            elif item.size == 'Size 5' and item.quantity > product.stock_large:
                messages.error(request, f'Insufficient stock for {product.product_name}.')
                stock_check_passed = False
                break

        if not stock_check_passed:
            return redirect('cart')  # Redirect to cart if stock is insufficient

      
        if payment_method == 'cash_on_delivery':
            # Handle Cash on Delivery
            checkoutdetails = CheckoutDetails.objects.filter(user=request.user).last()

            gt=checkoutdetails.grand_total
            if gt > 1000:
                messages.error(request, 'Orders above Rs 1000 cannot be placed with Cash on Delivery.')
                return redirect('checkout')  # Redirect to the checkout page or appropriate page
            order = Order(
                user=request.user,
                name=request.user.get_full_name(),
                email=request.user.email,
                total_price=total,
                tax=tax,
                grand_total=gt,
                payment_method=payment_method,
                status='Pending',
                shipping_fee = 50,
                address_line1=address.address,
                address_line2=address.address_line2,
                city=address.city,
                state=address.state,
                pincode=address.pincode,
                coupon_id=coupon_id
            )
            coupon_deduction = checkoutdetails.before_price - order.grand_total
    
            order.coupon_price = coupon_deduction

            order.order_number = order.generate_unique_order_number()

            with transaction.atomic():
                order.save()

                # Create order items and update product stock
                # Dictionary to hold stock adjustments for each product
                stock_adjustments = defaultdict(lambda: {'small': 0, 'medium': 0, 'large': 0})

                for item in cart_items:
                    # Create ordered items
                    OrderedItems.objects.create(
                        product=item.product,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        size=item.size,
                        order_number=order.order_number,
                        shipping_fee=order.shipping_fee
                    )
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        sub_total=item.sub_total(),
                    )
                    
                    # Adjust stock for this product based on size
                    if item.size == 'Size 3':
                        stock_adjustments[item.product]['small'] += item.quantity
                    elif item.size == 'Size 4':
                        stock_adjustments[item.product]['medium'] += item.quantity
                    elif item.size == 'Size 5':
                        stock_adjustments[item.product]['large'] += item.quantity

                # Update stock for each product only once
                for product, adjustments in stock_adjustments.items():
                    product.stock_small -= adjustments['small']
                    product.stock_medium -= adjustments['medium']
                    product.stock_large -= adjustments['large']
                    product.save()

                # No Payment entry needed for Cash on Delivery
                cart_items.delete()

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('order_successful')  # Ensure this path is correct

        elif payment_method == 'wallet':
            # Handle Wallet Payment
            checkoutdetails = CheckoutDetails.objects.filter(user=request.user).last()
            gt = checkoutdetails.grand_total
            order = Order(
                user=request.user,
                name=request.user.get_full_name(),
                email=request.user.email,
                total_price=total,
                tax=tax,
                grand_total=gt,
                payment_method=payment_method,
                status='Pending',
                shipping_fee=50,
                address_line1=address.address,
                address_line2=address.address_line2,
                city=address.city,
                state=address.state,
                pincode=address.pincode,
                coupon_id=coupon_id
            )
            coupon_deduction = checkoutdetails.before_price - order.grand_total
          
            order.coupon_price = coupon_deduction
            order.order_number = order.generate_unique_order_number()

            # Get user's wallet
            wallet = Wallet.objects.get(user=request.user)

            # Check if the wallet balance is sufficient
            if wallet.wallet_balance < gt:
                messages.error(request, 'Insufficient wallet balance.')
                return redirect('checkout')  # Redirect to the checkout page or another appropriate page
            
            with transaction.atomic():
                # Save order
                order.save()

                # Create order items and update product stock
                # Dictionary to hold stock adjustments for each product
                stock_adjustments = defaultdict(lambda: {'small': 0, 'medium': 0, 'large': 0})

                for item in cart_items:
                    # Create ordered items
                    OrderedItems.objects.create(
                        product=item.product,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        size=item.size,
                        order_number=order.order_number,
                        shipping_fee=order.shipping_fee
                    )
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        sub_total=item.sub_total(),
                    )
                    
                    # Adjust stock for this product based on size
                    if item.size == 'Size 3':
                        stock_adjustments[item.product]['small'] += item.quantity
                    elif item.size == 'Size 4':
                        stock_adjustments[item.product]['medium'] += item.quantity
                    elif item.size == 'Size 5':
                        stock_adjustments[item.product]['large'] += item.quantity

                # Update stock for each product only once
                for product, adjustments in stock_adjustments.items():
                    product.stock_small -= adjustments['small']
                    product.stock_medium -= adjustments['medium']
                    product.stock_large -= adjustments['large']
                    product.save()

              
                Payment.objects.create(
                    order=order,
                    payment_method=payment_method,
                    amount_paid=gt,  # Use grand_total as the amount paid
                )

                # Update wallet balance
                wallet.update_balance(transaction_type='debit', amount=gt)

                # Create wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=gt,
                    transaction_type='debit',
                    description=f'Order #{order.order_number}',
                )

                # Clear cart items
                cart_items.delete()

            messages.success(request, 'Your order has been placed successfully!')
            return redirect('order_successful')  # Ensure this path is correct


        else:

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            checkoutdetails = CheckoutDetails.objects.filter(user=request.user).last()
            gt = checkoutdetails.grand_total
            coupon_id=Coupon.objects.last()
            coupon_id.quantity-=1
            coupon_id.save()
            try:
                # Verify payment signature
                client.utility.verify_payment_signature(params_dict)
                payment_status = "success"
            except razorpay.errors.SignatureVerificationError as e:
                payment_status = "failure"
                messages.error(request, 'Razorpay payment failed. Please try again.')
                return redirect('checkout')

            if payment_status == "success":
                # Proceed with order creation
                order = Order(
                    user=request.user,
                    name=request.user.get_full_name(),
                    email=request.user.email,
                    total_price=total,
                    tax=tax,
                    grand_total=gt,
                    payment_method='Razor Pay',
                    status='Pending',
                    shipping_fee=50,
                    address_line1=address.address,
                    address_line2=address.address_line2,
                    city=address.city,
                    state=address.state,
                    pincode=address.pincode,
                   
                )
                coupon_deduction = checkoutdetails.before_price - order.grand_total
              
                order.coupon_price = coupon_deduction
                order.order_number = order.generate_unique_order_number()

                with transaction.atomic():
                    order.save()

                    # Create order items and update product stock
                # Dictionary to hold stock adjustments for each product
                stock_adjustments = defaultdict(lambda: {'small': 0, 'medium': 0, 'large': 0})

                for item in cart_items:
                    # Create ordered items
                    OrderedItems.objects.create(
                        product=item.product,
                        unit_price=item.unit_price,
                        quantity=item.quantity,
                        size=item.size,
                        order_number=order.order_number,
                        shipping_fee=order.shipping_fee
                    )
                    
                    # Create order item
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        sub_total=item.sub_total(),
                    )
                    
                    # Adjust stock for this product based on size
                    if item.size == 'Size 3':
                        stock_adjustments[item.product]['small'] += item.quantity
                    elif item.size == 'Size 4':
                        stock_adjustments[item.product]['medium'] += item.quantity
                    elif item.size == 'Size 5':
                        stock_adjustments[item.product]['large'] += item.quantity

                # Update stock for each product only once
                for product, adjustments in stock_adjustments.items():
                    product.stock_small -= adjustments['small']
                    product.stock_medium -= adjustments['medium']
                    product.stock_large -= adjustments['large']
                    product.save()

                    Payment.objects.create(
                        order=order,
                        payment_method=payment_method,
                        amount_paid=grand_total,
                    )

                    cart_items.delete()

                messages.success(request, 'Your order has been placed successfully!')
                return redirect('order_successful')  # Ensure this path is correct
    else:
        return redirect('cart')
from django.shortcuts import render, get_object_or_404
from django.db import transaction
from collections import defaultdict

# def retry_page(request):
#     # Fetch user's orders
#     orders = Order.objects.filter(user=request.user).order_by('-created_at')
#     checkoutdetails = CheckoutDetails.objects.filter(user=request.user).last()
#     cart_items = CartItem.objects.filter(user=request.user, is_active=True)

#     # Calculate totals
#     total = sum(item.sub_total() for item in cart_items)
#     tax = (2 * total) / 100
#     shipping_fee = 50
#     grand_total = total + tax + shipping_fee
#     payment_method = 'Razor Pay'

#     # Fetch the most recent checkout details
#     checkoutdetails = CheckoutDetails.objects.filter(user=request.user).last()
#     gt = checkoutdetails.grand_total if checkoutdetails else grand_total  # Fallback if no checkout details

#     # Only create an order if none exists with 'Payment Pending'
#     existing_order = Order.objects.filter(user=request.user, status='Payment Pending').last()
    
#     if not existing_order:
#         with transaction.atomic():
#             # Create a new order
#             order = Order(
#                 user=request.user,
#                 name=request.user.get_full_name(),
#                 email=request.user.email,
#                 total_price=total,
#                 tax=tax,
#                 grand_total=gt,
#                 payment_method=payment_method,
#                 status='Payment Pending',
#                 shipping_fee=shipping_fee
#             )
#             coupon_deduction = checkoutdetails.before_price - gt if checkoutdetails else 0
#             order.coupon_price = coupon_deduction
#             order.order_number = order.generate_unique_order_number()
#             order.save()

#             # Create ordered items and update stock
#             stock_adjustments = defaultdict(lambda: {'small': 0, 'medium': 0, 'large': 0})
#             for item in cart_items:
#                 OrderedItems.objects.create(
#                     product=item.product,
#                     unit_price=item.unit_price,
#                     quantity=item.quantity,
#                     size=item.size,
#                     order_number=order.order_number,
#                     shipping_fee=order.shipping_fee
#                 )
#                 OrderItem.objects.create(
#                     order=order,
#                     product=item.product,
#                     quantity=item.quantity,
#                     sub_total=item.sub_total(),
#                 )
                
#                 # Adjust stock based on size
#                 if item.size == 'Size 3':
#                     stock_adjustments[item.product]['small'] += item.quantity
#                 elif item.size == 'Size 4':
#                     stock_adjustments[item.product]['medium'] += item.quantity
#                 elif item.size == 'Size 5':
#                     stock_adjustments[item.product]['large'] += item.quantity

#             # Update stock for each product
#             for product, adjustments in stock_adjustments.items():
#                 product.stock_small -= adjustments['small']
#                 product.stock_medium -= adjustments['medium']
#                 product.stock_large -= adjustments['large']
#                 product.save()

#             # Clear cart items after placing the order
#             cart_items.delete()

#         print('Order created successfully!')

#     # Handle the Pay Now button
#     if request.method == "POST":
#         order_id = request.POST.get('order_id')
#         order = get_object_or_404(Order, id=order_id)

#         # Fetch user's addresses and ordered items
#         user_addresses = Address.objects.filter(user=request.user)
#         ordered_items = OrderedItems.objects.filter(order_number=order.order_number)
#         razorpay_order_id = None
#         client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
#         order_data = {
#             'amount': int(grand_total * 100),  # Amount in paise
#             'currency': 'INR',
#             'receipt': 'order_rcptid_11',
#             'payment_capture': '1'  # Automatic capture
#         }
#         razorpay_order = client.order.create(data=order_data)
#         razorpay_order_id = razorpay_order['id']
#         # Update total price for each ordered item
#         for ordered_item in ordered_items:
#             ordered_item.total_price = ordered_item.quantity * ordered_item.unit_price

#         context = {
#             'order': order,
#             'razorpay_order_id': razorpay_order_id,  # Pass the Razorpay order ID to the template
#             'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID,  # Pass the Razorpay Key ID to the template
#             'user_addresses': user_addresses,
#             'total': order.total_price,
#             'tax': order.tax,
#             'shipping_fee': order.shipping_fee,
#             'grand_total': order.grand_total,
#             'ordered_items': ordered_items,
            
#         }

#         return render(request, 'store/checkout2.html', context)

#     # Render the orders page if it's not a POST request
#     return render(request, 'accounts/my_orders.html', {'orders': orders})

def retry_page(request):
    # Fetch user's previous orders
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    cart_items = CartItem.objects.filter(user=request.user, is_active=True)
    
    # Calculate totals
    total = sum(item.sub_total() for item in cart_items)
    tax = (2 * total) / 100
    shipping_fee = 50
    grand_total = total + tax + shipping_fee
    payment_method = 'Razor Pay'

    # Fetch most recent checkout details
    checkoutdetails = CheckoutDetails.objects.filter(user=request.user).last()
    gt = checkoutdetails.grand_total if checkoutdetails else grand_total  # Fallback if no checkout details
    
    # Check if an existing order with 'Payment Pending' exists
    existing_order = Order.objects.filter(user=request.user, status='Payment Pending').last()

    # Reuse existing order if found
    if existing_order:
        order = existing_order
        order.grand_total = gt  # Update grand total if needed
        coupon_deduction = checkoutdetails.before_price - gt if checkoutdetails else 0
        order.coupon_price = coupon_deduction
        order.save()
    else:
        with transaction.atomic():
            # Create a new order if none exists
            order = Order(
                user=request.user,
                name=request.user.get_full_name(),
                email=request.user.email,
                total_price=total,
                tax=tax,
                grand_total=gt,
                payment_method=payment_method,
                status='Payment Pending',
                shipping_fee=shipping_fee
            )
            coupon_deduction = checkoutdetails.before_price - gt if checkoutdetails else 0
            order.coupon_price = coupon_deduction
            order.order_number = order.generate_unique_order_number()
            order.save()

            # Create ordered items and update stock
            stock_adjustments = defaultdict(lambda: {'small': 0, 'medium': 0, 'large': 0})
            for item in cart_items:
                OrderedItems.objects.create(
                    product=item.product,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    size=item.size,
                    order_number=order.order_number,
                    shipping_fee=order.shipping_fee
                )

                # Adjust stock
                if item.size == 'Size 3':
                    stock_adjustments[item.product]['small'] += item.quantity
                elif item.size == 'Size 4':
                    stock_adjustments[item.product]['medium'] += item.quantity
                elif item.size == 'Size 5':
                    stock_adjustments[item.product]['large'] += item.quantity

            # Update stock for each product
            for product, adjustments in stock_adjustments.items():
                product.stock_small -= adjustments['small']
                product.stock_medium -= adjustments['medium']
                product.stock_large -= adjustments['large']
                product.save()

            # Clear cart items after placing the order
            cart_items.delete()

        print('Order created successfully!')

    # Handle the Pay Now button
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        order = get_object_or_404(Order, id=order_id)

        # Fetch user's addresses and ordered items
        user_addresses = Address.objects.filter(user=request.user)
        ordered_items = OrderedItems.objects.filter(order_number=order.order_number)

        # Reuse existing Razorpay order ID if available
        if checkoutdetails and checkoutdetails.razorpay_order_id:
            razorpay_order_id = checkoutdetails.razorpay_order_id
        else:
            # Create a new Razorpay order if not already created
            client = Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            order_data = {
                'amount': int(grand_total * 100),  # Amount in paise
                'currency': 'INR',
                'receipt': 'order_rcptid_11',
                'payment_capture': '1'  # Automatic capture
            }
            razorpay_order = client.order.create(data=order_data)
            razorpay_order_id = razorpay_order['id']

            # Save the Razorpay order ID in CheckoutDetails
            if checkoutdetails:
                checkoutdetails.razorpay_order_id = razorpay_order_id
                checkoutdetails.save()
        for item in ordered_items:
            item.total = item.quantity * item.unit_price
        # Pass context to the template
        context = {
            'order': order,
            'razorpay_order_id': razorpay_order_id,
            'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID,
            'user_addresses': user_addresses,
            'total': order.total_price,
            'tax': order.tax,
            'shipping_fee': order.shipping_fee,
            'grand_total': order.grand_total,
            'ordered_items': ordered_items,
        }

        return render(request, 'store/checkout2.html', context)

    # Render the orders page if it's not a POST request
    return render(request, 'accounts/my_orders.html', {'orders': orders})




@login_required(login_url='login')
def place_order_two(request):
    if request.method == 'POST':
        # Razorpay client setup
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Get the payment details from the request
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        # Parameters for verifying the signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            # Verify payment signature
            client.utility.verify_payment_signature(params_dict)
            payment_status = "success"
        except razorpay.errors.SignatureVerificationError:
            payment_status = "failure"
            messages.error(request, 'Razorpay payment failed. Please try again.')
        
        # Regardless of payment status, set the order status to 'Pending'
        order = get_object_or_404(Order, order_number=razorpay_order_id, user=request.user)
        order.status = 'Pending'
        order.save()

        # Redirect to the success page
        return redirect('order_successful')

    # If not a POST request, redirect to checkout
    return redirect('checkout')



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Payment, Order  # Import your Payment and Order models
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from .models import Payment, Order

@csrf_protect
def process_payment(request):
    if request.method == 'POST':
        # Get payment details from POST request
        
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        order_id = request.POST.get('order_id')

        try:
            order = Order.objects.get(id=order_id)

            payment = Payment(
                order=order,
                payment_method='Razorpay',
                payment_status='Completed',
                amount_paid=order.total_amount,
                razorpay_payment_id=razorpay_payment_id,
                razorpay_order_id=razorpay_order_id,
                razorpay_signature=razorpay_signature
            )
            payment.save()

            return JsonResponse({'status': 'success', 'message': 'Payment processed successfully.'})

        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found.'}, status=404)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)





@login_required
def order_successful(request):
    latest_order = Order.objects.filter(user=request.user).latest('created_at')  # Adjust 'created_at' if needed

    # Update the status to 'Pending'
    latest_order.status = 'Pending'
    latest_order.save()

    if latest_order.coupon_id:
        # Retrieve the coupon by its ID
        coupon = Coupon.objects.get(id=latest_order.coupon_id)
        
        # Decrease the coupon quantity
        coupon.quantity -= 1
        coupon.save()
    
    # Render the order success page
    return render(request, 'orders/order_successful.html')

   




# def create_coupon(request):
#     if request.method == "POST":
#         code = request.POST.get('code')
#         description = request.POST.get('description')
#         discount_percentage = request.POST.get('discountPercentage')
#         min_purchase_amount = request.POST.get('minPurchaseAmount')
#         quantity = request.POST.get('quantity')
#         expiry_date = request.POST.get('expiryDate')

#         # Create a new Coupon instance and save it to the database
#         coupon = Coupon(
#             code=code,
#             description=description,
#             discount_percentage=discount_percentage,
#             minimum_purchase_amount=min_purchase_amount,
#             quantity=quantity,
#             expiry_date=expiry_date,
#             status='active',
#         )
#         coupon.save()

#         messages.success(request, 'Coupon created successfully!')
#         return redirect('admincoupons')


#     return render(request, 'admins/coupons.html')
def create_coupon(request):
    if request.method == "POST":
        code = request.POST.get('code')
        description = request.POST.get('description')
        discount_percentage = request.POST.get('discountPercentage')
        min_purchase_amount = request.POST.get('minPurchaseAmount')
        quantity = request.POST.get('quantity')
        expiry_date = request.POST.get('expiryDate')
        max_redeemable_value = request.POST.get('maxRedeemableValue')  # New field
        quantity = request.POST.get('quantity')
        # Check if a coupon with the same code already exists
        if Coupon.objects.filter(code=code).exists():
            messages.error(request, 'Coupon code already exists!', extra_tags='error')
        else:
            # Create a new Coupon instance and save it to the database
            coupon = Coupon(
                code=code,
                description=description,
                discount_percentage=discount_percentage,
                minimum_purchase_amount=min_purchase_amount,
                max_redeemable_value=max_redeemable_value,
                quantity=quantity,
                expiry_date=expiry_date,
                status='active',
            )
            coupon.save()
            messages.success(request, 'Coupon created successfully!', extra_tags='success')
        
        return redirect('admincoupons')

    return render(request, 'admins/coupons.html')



def toggle_coupon_status(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if coupon.action == 'block':
        coupon.status = 'inactive'
        coupon.action = 'unblock'
        messages.success(request, 'Coupon Blocked successfully!', extra_tags='error')
    else:
        coupon.status = 'active'
        coupon.action = 'block'
        messages.success(request, 'Coupon Unblocked successfully!', extra_tags='success')
    coupon.save()
    return redirect('admincoupons')  # Redirect to the view that lists all coupons
import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import Coupon
from carts.models import CheckoutDetails

logger = logging.getLogger(__name__)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from carts.models import CheckoutDetails
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def apply_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            coupon_code = data.get('coupon_code')
            
            coupon = get_object_or_404(Coupon, code=coupon_code, status='active')
            request.session['coupon_id'] = coupon.id
            
            # Check if the coupon has expired
            if coupon.expiry_date < timezone.now().date():
                return JsonResponse({'success': False, 'message': "This coupon has expired."})
            
            # Check if the coupon is redeemable
            if coupon.quantity <= 0:
                return JsonResponse({'success': False, 'message': "This coupon is no longer available."})
            
            order = CheckoutDetails.objects.filter(user=request.user).last()
            
            if not order:
                return JsonResponse({'success': False, 'message': "No active order found."})
            
            # Check if the order meets the minimum purchase amount
            if order.grand_total < coupon.minimum_purchase_amount:
                return JsonResponse({'success': False, 'message': f"Order amount does not meet the minimum purchase amount of ₹{coupon.minimum_purchase_amount} for this coupon."})
            
            # Calculate discount amount and check against max redeemable value
            discount_amount = (coupon.discount_percentage / 100) * order.grand_total
            if coupon.max_redeemable_value is not None:
                discount_amount = min(discount_amount, coupon.max_redeemable_value)
            
            # Apply discount and update order
            order.grand_total -= discount_amount
            order.coupon = coupon
            order.coupon_applied = True
            order.save()
            
         
            coupon.save()
            
            # Log success
            logger.info(f"Coupon {coupon_code} applied successfully to order {order.id}. Coupon ID: {coupon.id}")
            logger.info(f"Order details after applying coupon: Grand Total: {order.grand_total}, Coupon Applied: {order.coupon_applied}, Coupon ID: {order.coupon_id}")
            
            return JsonResponse({'success': True, 'new_grand_total': round(order.grand_total, 2)})
        
        except Coupon.DoesNotExist:
            logger.warning(f"Invalid coupon code attempted: {coupon_code}")
            return JsonResponse({'success': False, 'message': "Invalid coupon code."})
        except Exception as e:
            logger.error(f"Error in apply_coupon: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'message': "Invalid coupon"})
    
    return JsonResponse({'success': False, 'message': "Invalid request."})
@csrf_exempt
def remove_coupon(request):
    if request.method == 'POST':
        try:
            # Retrieve the active order (CheckoutDetails) for the current user where a coupon was applied
            order = CheckoutDetails.objects.filter(user=request.user, coupon_applied=True).last()
            
            if not order:
                return JsonResponse({'success': False, 'message': "No coupon applied or no active order found."})
            
            if order.coupon is None:
                logger.error(f"Coupon is None for order {order.id}")
                return JsonResponse({'success': False, 'message': "Coupon information is missing."})
            
            # Calculate the original grand total (before discount)
            discount_percentage = order.coupon.discount_percentage
            original_grand_total = order.grand_total / (1 - (discount_percentage / 100))
            
            # Ensure that the original grand total is valid
            if original_grand_total <= 0:
                logger.error(f"Invalid grand total calculation for order {order.id}")
                return JsonResponse({'success': False, 'message': "Invalid grand total calculation."})

            # Update the order
            order.grand_total = original_grand_total
            order.coupon_applied = False
            coupon = order.coupon  # Store the coupon to update later
            order.coupon = None  # Remove the coupon relationship
            order.save()
            
            # Increase the coupon quantity
            if coupon:
                
                coupon.save()
                logger.info(f"Coupon quantity increased for coupon {coupon.id}")
            
            logger.info(f"Coupon removed successfully for order {order.id}")
            return JsonResponse({'success': True, 'new_grand_total': round(order.grand_total, 2)})
        
        except Exception as e:
            logger.error(f"Error in remove_coupon: {str(e)}", exc_info=True)
            return JsonResponse({'success': False, 'message': "An error occurred while removing the coupon."})
    
    return JsonResponse({'success': False, 'message': "Invalid request."})



# def check_coupon_status(request):
#     if request.method == 'GET':
#         try:
#             order = CheckoutDetails.objects.filter(user=request.user, coupon_applied=True).last()
#             if order and order.coupon:
#                 return JsonResponse({
#                     'success': True,
#                     'coupon_applied': True,
#                     'grand_total': round(order.grand_total, 2),
#                     'coupon_code': order.coupon.code
#                 })
#             else:
#                 return JsonResponse({'success': True, 'coupon_applied': False})
#         except Exception as e:
#             logger.error(f"Error in check_coupon_status: {str(e)}")
#             return JsonResponse({'success': False, 'message': "An error occurred while checking coupon status."})

#     return JsonResponse({'success': False, 'message': "Invalid request."})

def check_coupon_status(request):
    if request.method == 'GET':
        try:
            order = CheckoutDetails.objects.filter(user=request.user).last()
            if order and order.coupon_applied:
                original_total = order.grand_total / (1 - (order.coupon.discount_percentage / 100))
                return JsonResponse({
                    'success': True,
                    'coupon_applied': True,
                    'original_total': round(original_total, 2),
                    'grand_total': round(order.grand_total, 2),
                    'coupon_code': order.coupon.code
                })
            else:
                return JsonResponse({
                    'success': True,
                    'coupon_applied': False,
                    'grand_total': round(order.grand_total, 2) if order else 0
                })
        except Exception as e:
            logger.error(f"Error in check_coupon_status: {str(e)}")
            return JsonResponse({'success': False, 'message': "An error occurred while checking coupon status."})

    return JsonResponse({'success': False, 'message': "Invalid request."})