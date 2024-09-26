from .models import Product

def counter(request):
    wishlist_count = 0

    if 'admin' in request.path:
        return {}
    else:
        if request.user.is_authenticated:
            # Count the total number of products marked as wishlisted
            wishlist_count = Product.objects.filter(wishlisted=True).count()

            # Update the wishlist_count field for each wishlisted product
            wishlisted_products = Product.objects.filter(wishlisted=True)
            for product in wishlisted_products:
                product.wishlist_count = wishlist_count
                product.save()

        else:
            # For unauthenticated users, wishlist count is zero
            wishlist_count = 0

    return dict(wishlist_count=wishlist_count)
