from .models import Category

def menu_links(request):
    links = Category.objects.filter(is_available=True)  # Filter out not available categories
    return dict(links=links)