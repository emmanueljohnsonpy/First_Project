from django.shortcuts import render
from store.models import Product, ReviewRating
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy

def user_required(user):
    return not user.is_staff and not user.is_superuser

user_login_required = user_passes_test(user_required, login_url=reverse_lazy('login'))

@user_login_required
def home(request):
    # products = Product.objects.all().filter(is_available=True).order_by('created_date')
    products = Product.objects.filter(is_available=True, category__is_available=True).order_by('created_date')

    # Get the reviews
    reviews = None
    for product in products:
        reviews = ReviewRating.objects.filter(product_id=product.id, status=True)

    context = {
        'products': products,
        'reviews': reviews,
    }
    return render(request, 'home.html', context)
