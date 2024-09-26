from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ReviewRating, ProductGallery
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse
from django.db.models import Q
from .forms import ReviewForm  
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from .models import Product, Category
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.contrib.auth.decorators import login_required
# from .models import Variation
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse_lazy

def user_required(user):
    return not user.is_staff and not user.is_superuser

user_login_required = user_passes_test(user_required, login_url=reverse_lazy('login'))

from django.http import JsonResponse

from django.utils import timezone

# def store(request, category_slug=None):
#     categories = None
#     products = None

#     sort_by = request.GET.get('sort', 'new-arrivals')
    
#     if category_slug != None:
#         categories = get_object_or_404(Category, slug=category_slug, is_available=True)
#         products = Product.objects.filter(category=categories, is_available=True)
#         if sort_by == 'price-high-low':
#             products = products.order_by('-price')
#         elif sort_by == 'price-low-high':
#             products = products.order_by('price')
#         elif sort_by == 'average-ratings':
#             products = products.annotate(average_rating=Avg('reviewrating__rating')).order_by('-average_rating')
#         elif sort_by == 'popularity':
#             products = products.annotate(review_count=Count('reviewrating')).order_by('-review_count')
#         elif sort_by == 'az':
#             products = products.order_by('product_name')
#         elif sort_by == 'za':
#             products = products.order_by('-product_name')
#         else:  # Default is 'new-arrivals'
#             products = products.order_by('-created_date')
#         paginator = Paginator(products, 3)
#         page = request.GET.get('page')
#         paged_products = paginator.get_page(page)
#         product_count = products.count()
#     else:
#         products = Product.objects.all().filter(is_available=True, category__is_available=True).order_by('id')
#         if sort_by == 'price-high-low':
#             products = products.order_by('-price')
#         elif sort_by == 'price-low-high':
#             products = products.order_by('price')
#         elif sort_by == 'average-ratings':
#             products = products.annotate(average_rating=Avg('reviewrating__rating')).order_by('-average_rating')
#         elif sort_by == 'popularity':
#             products = products.annotate(review_count=Count('reviewrating')).order_by('-review_count')
#         elif sort_by == 'az':
#             products = products.order_by('product_name')
#         elif sort_by == 'za':
#             products = products.order_by('-product_name')
#         else:  # Default is 'new-arrivals'
#             products = products.order_by('-created_date')

#         paginator = Paginator(products, 3)
#         page = request.GET.get('page')
#         paged_products = paginator.get_page(page)
#         product_count = products.count()

#     context = {
#         'products': paged_products,
#         'product_count': product_count,
#         'sort_by': sort_by,
#     }
#     return render(request, 'store/store.html', context) 
from django.db.models import F, Sum
@user_login_required
def store(request, category_slug=None):
    categories = None
    products = None
    
    sort_by = request.GET.get('sort')
    
    # Base queryset without stock filter
    base_queryset = Product.objects.filter(
        is_available=True, 
        category__is_available=True
    )

    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug, is_available=True)
        products = base_queryset.filter(category=categories)
    else:
        products = base_queryset

    # Apply sorting and hide out-of-stock products only if sort_by is specified
    if sort_by:
        products = products.annotate(
            total_stock=Sum(F('stock_small') + F('stock_medium') + F('stock_large'))
        ).filter(total_stock__gt=0)

        if sort_by == 'price-high-low':
            products = products.order_by('-price')
        elif sort_by == 'price-low-high':
            products = products.order_by('price')
        elif sort_by == 'average-ratings':
            products = products.annotate(average_rating=Avg('reviewrating__rating')).order_by('-average_rating')
        elif sort_by == 'popularity':
            products = products.annotate(review_count=Count('reviewrating')).order_by('-review_count')
        elif sort_by == 'az':
            products = products.order_by('product_name')
        elif sort_by == 'za':
            products = products.order_by('-product_name')
        elif sort_by == 'new-arrivals':
            products = products.order_by('-created_date')
    else:
        # Default sorting without hiding out-of-stock products
        products = products.order_by('-created_date')

    paginator = Paginator(products, 3)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
        'sort_by': sort_by,
    }
    return render(request, 'store/store.html', context)

@user_login_required
def product_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Product.DoesNotExist:
        # Handle the case where the product does not exist
        return render(request, '404.html', status=404)
    except Exception as e:
        # Handle other exceptions if needed
        raise e

    # if request.user.is_authenticated:
    #     try:
    #         orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
    #     except OrderProduct.DoesNotExist:
    #         orderproduct = None
    # else:
    #     orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)
    related_products = Product.objects.filter(category=single_product.category).exclude(id=single_product.id)

    # Add size-based stock values to the context
    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        # 'orderproduct': orderproduct,
        'reviews': reviews,
        'related_products': related_products,
        'product_gallery': product_gallery,
        'stock_small': single_product.stock_small,
        'stock_medium': single_product.stock_medium,
        'stock_large': single_product.stock_large,
        'total_stock': single_product.get_total_stock(),
    }
    return render(request, 'store/product_detail.html', context)

from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
@login_required(login_url='login')
@user_login_required
def search(request):
    products = Product.objects.none()  # Initialize with an empty queryset
    product_count = 0
    keyword = request.GET.get('keyword', '').strip()
    sort_by = request.GET.get('sort_by', '')

    if keyword:
        products = Product.objects.filter(
            Q(description__icontains=keyword) | Q(product_name__icontains=keyword),
            is_available=True,
            category__is_available=True
        )

        # Sorting logic
        if sort_by == 'name_asc':
            products = products.order_by('product_name')  # A to Z
        elif sort_by == 'name_desc':
            products = products.order_by('-product_name')  # Z to A
        elif sort_by == 'price_asc':
            products = products.order_by('price')  # Low to High
        elif sort_by == 'price_desc':
            products = products.order_by('-price')  # High to Low
        # elif sort_by == 'new_arrivals':
        #     products = products.order_by('-created_date')  # New Arrivals (latest created date)
        # elif sort_by == 'featured':
        #     products = products.filter(is_featured=True)  # Assuming there's an `is_featured` field
        # elif sort_by == 'popularity':
        #     products = products.annotate(num_sales=Count('order')).order_by('-num_sales')  # Popularity by sales (assuming there's an Order model)
        # elif sort_by == 'average_ratings':
        #     products = products.annotate(avg_rating=Avg('review__rating')).order_by('-avg_rating')  # Average ratings from the Review model

        product_count = products.count()

    context = {
        'products': products,
        'product_count': product_count,
    }

    return render(request, 'store/searched_product.html', context)


def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
            


def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            if product.wishlisted:
                # Remove from wishlist
                product.wishlisted = False
                product.wishlist_added_date = None
                product.wishlist_count -= 1
            else:
                # Add to wishlist
                product.wishlisted = True
                product.wishlist_added_date = timezone.now()  # Ensure you import timezone
                product.wishlist_count += 1
            product.save()
            return JsonResponse({'success': True, 'wishlisted': product.wishlisted, 'wishlist_count': product.wishlist_count})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})



@user_login_required
def wishlist(request):
    # Filter products that are wishlisted and order them by the date they were added to the wishlist
    wishlisted_products = Product.objects.filter(wishlisted=True).order_by('-wishlist_added_date')
    return render(request, 'store/wishlist.html', {'products': wishlisted_products})




def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.wishlisted = False
    product.save()

    return redirect('wishlist')  # Redirect to the wishlist page after removal

