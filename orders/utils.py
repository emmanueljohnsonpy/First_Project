from store.models import Product
# utils.py or another appropriate file
def get_cart_items(request):
    # Assuming cart items are stored in session
    cart = request.session.get('cart', {})
    cart_items = []
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        cart_items.append({
            'product': product,
            'quantity': quantity,
            'sub_total': product.price * quantity
        })
    return cart_items
