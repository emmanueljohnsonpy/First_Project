from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from store.models import Product
from accounts.models import Account
from category.models import Category
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.sessions.models import Session
from django.contrib.auth import login as auth_login, logout as auth_logout, authenticate
from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.sessions.models import Session
from django.utils.text import slugify
from django.http import HttpResponse
from django.contrib.auth import logout
from orders.models import Order
from django.contrib.sessions.models import Session
from orders.models import Coupon
from store.models import Offer
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q



def adminlogin(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(request, email=email, password=password)
        
        if user is not None:
            if user.is_staff or user.is_superuser:
                # Ensure the user is not logged in on the user side
                user_session_key = request.session.get('user_session_key')
                if user_session_key:
                    try:
                        session = Session.objects.get(pk=user_session_key)
                        session.delete()
                    except Session.DoesNotExist:
                        pass  # Ignore if the session doesn't exist

                auth_logout(request)  # Clear any existing session
                auth_login(request, user)  # Log in the admin user

                # Set a flag in the session to differentiate the admin session
                request.session['is_admin'] = True
                request.session['admin_session_key'] = request.session.session_key
                
                return redirect('admindashboard')
            else:
                messages.error(request, 'You are not authorized to access this page.')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'admins/login.html')
from django.contrib.auth.decorators import user_passes_test
def admin_required(user):
    return user.is_staff or user.is_superuser



from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum
from django.urls import reverse_lazy
from django.db.models.functions import ExtractMonth, ExtractYear
import json
from calendar import monthrange

from django.db.models.functions import TruncDate

def get_filtered_data(start_date, end_date):
    orders = Order.objects.filter(
        created_at__range=[start_date, end_date]
    ).exclude(
        status__in=['Return Pending', 'Return Success']
    )

    daily_totals = orders.annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('grand_total')
    ).order_by('date')

    return daily_totals


def get_year_totals(start_year, end_year):
    year_totals = {}
    for year in range(start_year, end_year + 1):
        start_of_year = timezone.make_aware(timezone.datetime(year, 1, 1))
        end_of_year = timezone.make_aware(timezone.datetime(year, 12, 31, 23, 59, 59))
        
        # Filter orders within the specific year
        # orders = Order.objects.filter(created_at__range=[start_of_year, end_of_year])
        orders = Order.objects.filter(
            created_at__range=[start_of_year, end_of_year]
        ).exclude(
            status__in=['Return Pending', 'Return Success']
        )
        # Calculate the total grand_total for the year
        year_total = orders.aggregate(total=Sum('grand_total'))['total'] or 0
        year_totals[year] = year_total
    
    return year_totals


def get_year_month_dates(now):
    start_of_year = now.replace(month=1, day=1)
    end_of_year = now.replace(month=12, day=31)
    return start_of_year, end_of_year

def get_grand_totals_by_month():
    now = timezone.localtime(timezone.now())
    start_of_year, end_of_year = get_year_month_dates(now)
    
    # Filter orders within the current year
    # orders = Order.objects.filter(created_at__range=[start_of_year, end_of_year])
    # Filter orders within the current year, excluding 'Return Pending' and 'Return Success'
    orders = Order.objects.filter(
        created_at__range=[start_of_year, end_of_year]
    ).exclude(
        status__in=['Return Pending', 'Return Success']
    )
    # Initialize a dictionary to hold monthly totals
    month_totals = {month: 0 for month in range(1, 13)}
    
    # Calculate the total grand_total for each month
    for month in month_totals.keys():
        month_start = now.replace(month=month, day=1)
        month_end = month_start.replace(day=monthrange(now.year, month)[1])
        monthly_total = orders.filter(created_at__range=[month_start, month_end]).aggregate(total=Sum('grand_total'))['total'] or 0
        month_totals[month] = monthly_total
    
    return month_totals


def get_week_dates(now):
    start_of_week = now - timezone.timedelta(days=now.weekday())
    end_of_week = start_of_week + timezone.timedelta(days=6)
    return start_of_week, end_of_week

def get_grand_totals_by_day():
    now = timezone.localtime(timezone.now())
    start_of_week, end_of_week = get_week_dates(now)
    
    # Filter orders within the current week
    # orders = Order.objects.filter(created_at__range=[start_of_week, end_of_week])
    # Filter orders within the current week excluding 'Return Pending' and 'Return Success'
    orders = Order.objects.filter(
        created_at__range=[start_of_week, end_of_week]
    ).exclude(
        status__in=['Return Pending', 'Return Success']
    )
    # Annotate each day with total grand_total
    day_totals = {
        'Monday': orders.filter(created_at__week_day=1).aggregate(total=Sum('grand_total'))['total'] or 0,
        'Tuesday': orders.filter(created_at__week_day=2).aggregate(total=Sum('grand_total'))['total'] or 0,
        'Wednesday': orders.filter(created_at__week_day=3).aggregate(total=Sum('grand_total'))['total'] or 0,
        'Thursday': orders.filter(created_at__week_day=4).aggregate(total=Sum('grand_total'))['total'] or 0,
        'Friday': orders.filter(created_at__week_day=5).aggregate(total=Sum('grand_total'))['total'] or 0,
        'Saturday': orders.filter(created_at__week_day=6).aggregate(total=Sum('grand_total'))['total'] or 0,
        'Sunday': orders.filter(created_at__week_day=7).aggregate(total=Sum('grand_total'))['total'] or 0,
    }
    
    return day_totals



@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def admindashboard(request):
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if start_date_str and end_date_str:
        start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = timezone.datetime.strptime(end_date_str, '%Y-%m-%d').date()
        filtered_data = get_filtered_data(start_date, end_date)
        
        labels = [item['date'].strftime('%Y-%m-%d') for item in filtered_data]
        values = [float(item['total']) for item in filtered_data]
    else:
        labels = []
        values = []
    weekly_totals = get_grand_totals_by_day()
    
    monday_total = int(weekly_totals['Monday'])
    tuesday_total = int(weekly_totals['Tuesday'])
    wednesday_total = int(weekly_totals['Wednesday'])
    thursday_total = int(weekly_totals['Thursday'])
    friday_total = int(weekly_totals['Friday'])
    saturday_total = int(weekly_totals['Saturday'])
    sunday_total = int(weekly_totals['Sunday'])
    
    monthly_totals = get_grand_totals_by_month()
    
    jan_total = monthly_totals.get(1, 0)
    feb_total = monthly_totals.get(2, 0)
    mar_total = monthly_totals.get(3, 0)
    apr_total = monthly_totals.get(4, 0)
    may_total = monthly_totals.get(5, 0)
    jun_total = monthly_totals.get(6, 0)
    jul_total = monthly_totals.get(7, 0)
    aug_total = monthly_totals.get(8, 0)
    sep_total = monthly_totals.get(9, 0)
    oct_total = monthly_totals.get(10, 0)
    nov_total = monthly_totals.get(11, 0)
    dec_total = monthly_totals.get(12, 0)

    start_year = 2018
    end_year = 2024
    
    yearly_totals = get_year_totals(start_year, end_year)
    
    total_2018 = yearly_totals.get(2018, 0)
    total_2019 = yearly_totals.get(2019, 0)
    total_2020 = yearly_totals.get(2020, 0)
    total_2021 = yearly_totals.get(2021, 0)
    total_2022 = yearly_totals.get(2022, 0)
    total_2023 = yearly_totals.get(2023, 0)
    total_2024 = yearly_totals.get(2024, 0)

    day_data = [monday_total, tuesday_total, wednesday_total, thursday_total, friday_total, saturday_total, sunday_total]
    month_data = [int(jan_total), int(feb_total), int(mar_total), int(apr_total), int(may_total), int(jun_total), int(jul_total), int(aug_total), int(sep_total), int(oct_total), int(nov_total), int(dec_total)]
    year_data = [int(total_2018), int(total_2019), int(total_2020), int(total_2021), int(total_2022), int(total_2023), int(total_2024)]
    
    current_user = request.user

    time_filter = request.GET.get('filter', None)
    start_date_str = request.GET.get('start_date', None)
    end_date_str = request.GET.get('end_date', None)
    now = timezone.localtime(timezone.now())
    
    orders = Order.objects.all().order_by('-created_at')
    total_sales_count = orders.count()
    total_revenue = orders.aggregate(total=Sum('grand_total'))['total'] or 0
    coupon_deduction = orders.aggregate(total=Sum('coupon_price'))['total'] or 0
    total_old_price = Product.objects.aggregate(total=Sum('old_price'))['total'] or 0
    total_new_price = Product.objects.aggregate(total=Sum('price'))['total'] or 0
    total_discount = total_old_price - total_new_price

    top_products = OrderedItems.objects.values('product__product_name') \
        .annotate(total_ordered=Sum('quantity')) \
        .order_by('-total_ordered')[:10]
    top_categories = OrderedItems.objects.values('product__category__category_name') \
        .annotate(total_ordered=Sum('quantity')) \
        .order_by('-total_ordered')[:10]
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() + timedelta(days=1)
            orders = orders.filter(created_at__date__gte=start_date, created_at__date__lt=end_date)
        except ValueError:
            pass
    elif time_filter:
        if time_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_week':
            start_date = now - timedelta(days=now.weekday() + 7)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_month':
            start_date = now.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_year':
            start_date = now.replace(month=1, day=1) - timedelta(days=1)
            start_date = start_date.replace(month=1, day=1)
            orders = orders.filter(created_at__gte=start_date)

    # Apply pagination
    paginator = Paginator(orders, 10)  # 10 orders per page
    page_number = request.GET.get('page')
    paginated_orders = paginator.get_page(page_number)

    return render(request, 'admins/dashboard.html', {
        'orders': paginated_orders,  # Use paginated orders
        'total_revenue': total_revenue,
        'total_sales_count': total_sales_count,
        'total_discount': total_discount,
        'coupon_deduction': coupon_deduction,
        'current_user': current_user,
        'top_products': top_products,
        'top_categories': top_categories,
        'day_data': json.dumps(day_data),
        'month_data': json.dumps(month_data),
        'year_data': json.dumps(year_data),
        'filtered_labels': json.dumps(labels),
        'filtered_values': json.dumps(values),
    })

# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def admindashboard(request):
#     weekly_totals = get_grand_totals_by_day()
    
#     monday_total = int(weekly_totals['Monday'])
#     tuesday_total = int(weekly_totals['Tuesday'])
#     wednesday_total = int(weekly_totals['Wednesday'])
#     thursday_total = int(weekly_totals['Thursday'])
#     friday_total = int(weekly_totals['Friday'])
#     saturday_total = int(weekly_totals['Saturday'])
#     sunday_total = int(weekly_totals['Sunday'])
#     monthly_totals = get_grand_totals_by_month()
    
#     # Assign each month's total to a separate variable
#     jan_total = monthly_totals.get(1, 0)
#     feb_total = monthly_totals.get(2, 0)
#     mar_total = monthly_totals.get(3, 0)
#     apr_total = monthly_totals.get(4, 0)
#     may_total = monthly_totals.get(5, 0)
#     jun_total = monthly_totals.get(6, 0)
#     jul_total = monthly_totals.get(7, 0)
#     aug_total = monthly_totals.get(8, 0)
#     sep_total = monthly_totals.get(9, 0)
#     oct_total = monthly_totals.get(10, 0)
#     nov_total = monthly_totals.get(11, 0)
#     dec_total = monthly_totals.get(12, 0)

#     start_year = 2018
#     end_year = 2024
    
#     # Calculate the yearly totals
#     yearly_totals = get_year_totals(start_year, end_year)
    
#     # Assign each year's total to a separate variable
#     total_2018 = yearly_totals.get(2018, 0)
#     total_2019 = yearly_totals.get(2019, 0)
#     total_2020 = yearly_totals.get(2020, 0)
#     total_2021 = yearly_totals.get(2021, 0)
#     total_2022 = yearly_totals.get(2022, 0)
#     total_2023 = yearly_totals.get(2023, 0)
#     total_2024 = yearly_totals.get(2024, 0)

#     day_data = [monday_total, tuesday_total, wednesday_total, thursday_total, friday_total, saturday_total, sunday_total]
#     month_data = [int(jan_total), int(feb_total), int(mar_total), int(apr_total), int(may_total), int(jun_total), int(jul_total), int(aug_total), int(sep_total), int(oct_total), int(nov_total), int(dec_total)]
#     year_data = [int(total_2018), int(total_2019), int(total_2020), int(total_2021), int(total_2022), int(total_2023), int(total_2024)]
#     current_user=request.user
#     # Get the filter parameter from the request (e.g., 'today', 'last_week', etc.)
#     time_filter = request.GET.get('filter', None)
#     start_date_str = request.GET.get('start_date', None)
#     end_date_str = request.GET.get('end_date', None)
#     now = timezone.localtime(timezone.now())  # Get the current time in Asia/Kolkata
#     # Initialize the orders query
#     orders = Order.objects.all().order_by('-created_at')
#     total_sales_count = orders.count()

#     total_revenue = orders.aggregate(total=Sum('grand_total'))['total'] or 0
#     coupon_deduction = orders.aggregate(total=Sum('coupon_price'))['total'] or 0

#     total_old_price = Product.objects.aggregate(total=Sum('old_price'))['total'] or 0
#     total_new_price = Product.objects.aggregate(total=Sum('price'))['total'] or 0
#     total_discount = total_old_price - total_new_price
#     print(total_old_price)
#     print(total_new_price)
#     top_products = OrderedItems.objects.values('product__product_name') \
#         .annotate(total_ordered=Sum('quantity')) \
#         .order_by('-total_ordered')[:10]
#     top_categories = OrderedItems.objects.values('product__category__category_name') \
#         .annotate(total_ordered=Sum('quantity')) \
#         .order_by('-total_ordered')[:10]
#     if start_date_str and end_date_str:
#         try:
#             # Parse the dates from the strings
#             start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#             end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

#             # Adjust end_date to include the whole day
#             end_date = end_date + timedelta(days=1)

#             # Filter orders between the start and end dates
#             orders = orders.filter(created_at__date__gte=start_date, created_at__date__lt=end_date)
#         except ValueError:
#             # If the dates are not valid, handle it gracefully
#             pass
#     elif time_filter:
#         # If a predefined filter is applied, determine the start date for filtering
#         if time_filter == 'today':
#             start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
#             orders = orders.filter(created_at__gte=start_date)
#         elif time_filter == 'last_week':
#             start_date = now - timedelta(days=now.weekday() + 7)
#             orders = orders.filter(created_at__gte=start_date)
#         elif time_filter == 'last_month':
#             start_date = now.replace(day=1) - timedelta(days=1)
#             start_date = start_date.replace(day=1)
#             orders = orders.filter(created_at__gte=start_date)
#         elif time_filter == 'last_year':
#             start_date = now.replace(month=1, day=1) - timedelta(days=1)
#             start_date = start_date.replace(month=1, day=1)
#             orders = orders.filter(created_at__gte=start_date)
        
#     return render(request, 'admins/dashboard.html', {'orders': orders, 'total_revenue': total_revenue, 'total_sales_count': total_sales_count, 'total_discount': total_discount, 'coupon_deduction':coupon_deduction, 'current_user': current_user, 'top_products': top_products, 'top_categories': top_categories,
#         'day_data': json.dumps(day_data),
#         'month_data': json.dumps(month_data),
#         'year_data': json.dumps(year_data),})


from reportlab.lib.units import inch
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import pytz
# def generate_pdf(request):
#     buffer = BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=letter)
#     elements = []

#     now = timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))
#     time_filter = request.GET.get('filter', None)
#     start_date_str = request.GET.get('start_date', None)
#     end_date_str = request.GET.get('end_date', None)

#     orders = Order.objects.all().order_by('-created_at')
#     total_sales_count = orders.count()
#     total_revenue = orders.aggregate(total=Sum('grand_total'))['total'] or 0
#     coupon_deduction = orders.aggregate(total=Sum('coupon_price'))['total'] or 0
#     total_old_price = Product.objects.aggregate(total=Sum('old_price'))['total'] or 0
#     total_new_price = Product.objects.aggregate(total=Sum('price'))['total'] or 0
#     total_discount = total_old_price - total_new_price

#     # Apply date filters
#     if start_date_str and end_date_str:
#         try:
#             # Parse the dates from the strings
#             start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
#             end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

#             # Adjust end_date to include the whole day
#             end_date = end_date + timedelta(days=1)

#             # Filter orders between the start and end dates
#             orders = orders.filter(created_at__date__gte=start_date, created_at__date__lt=end_date)
#         except ValueError:
#             # If the dates are not valid, handle it gracefully
#             pass
#     elif time_filter:
#         # If a predefined filter is applied, determine the start date for filtering
#         if time_filter == 'today':
#             start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
#             orders = orders.filter(created_at__gte=start_date)
#         elif time_filter == 'last_week':
#             start_date = now - timedelta(days=now.weekday() + 7)
#             orders = orders.filter(created_at__gte=start_date)
#         elif time_filter == 'last_month':
#             start_date = now.replace(day=1) - timedelta(days=1)
#             start_date = start_date.replace(day=1)
#             orders = orders.filter(created_at__gte=start_date)
#         elif time_filter == 'last_year':
#             start_date = now.replace(month=1, day=1) - timedelta(days=1)
#             start_date = start_date.replace(month=1, day=1)
#             orders = orders.filter(created_at__gte=start_date)

#     # Create a table for the orders
#     data = [['Order ID', 'Customer', 'Email', 'Status', 'Total', 'Date']]
#     for order in orders:
#         email = getattr(order, 'user', 'N/A')  
#         name = getattr(order, 'name', 'N/A') 
#         status = getattr(order, 'status', 'N/A') 
#         created_at = getattr(order, 'created_at', 'N/A') 
#         data.append([
#             str(order.order_number),
#             name,
#             email,
#             status,
#             f"{order.grand_total:.2f} Rs",
#             created_at
#         ])

#     table = Table(data)
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, 0), 12),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('TOPPADDING', (0, 1), (-1, -1), 8),
#     ]))

#     # Add the title and table to the elements
#     styles = getSampleStyleSheet()
#     title = """
#     Sales Report
#     """
#     elements.append(Paragraph(title, styles['Title']))
#     elements.append(Spacer(1, 0.5*inch))
#     elements.append(table)
#     elements.append(Spacer(1, 0.25*inch))
   

#     doc.build(elements)

#     buffer.seek(0)
#     pdf = buffer.getvalue()
#     buffer.close()

#     response = HttpResponse(pdf, content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
#     return response
def generate_pdf(request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    now = timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))
    time_filter = request.GET.get('filter', None)
    start_date_str = request.GET.get('start_date', None)
    end_date_str = request.GET.get('end_date', None)

    orders = Order.objects.all().order_by('-created_at')
    
    # Calculate totals
    total_sales_count = orders.count()
    total_revenue = orders.aggregate(total=Sum('grand_total'))['total'] or 0
    coupon_deduction = orders.aggregate(total=Sum('coupon_price'))['total'] or 0
    total_old_price = Product.objects.aggregate(total=Sum('old_price'))['total'] or 0
    total_new_price = Product.objects.aggregate(total=Sum('price'))['total'] or 0
    total_discount = total_old_price - total_new_price

    # Apply date filters
    if start_date_str and end_date_str:
        try:
            # Parse the dates from the strings
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            # Adjust end_date to include the whole day
            end_date = end_date + timedelta(days=1)

            # Filter orders between the start and end dates
            orders = orders.filter(created_at__date__gte=start_date, created_at__date__lt=end_date)
        except ValueError:
            # If the dates are not valid, handle it gracefully
            pass
    elif time_filter:
        # If a predefined filter is applied, determine the start date for filtering
        if time_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_week':
            start_date = now - timedelta(days=now.weekday() + 7)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_month':
            start_date = now.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_year':
            start_date = now.replace(month=1, day=1) - timedelta(days=1)
            start_date = start_date.replace(month=1, day=1)
            orders = orders.filter(created_at__gte=start_date)

    # Create a table for the orders
    data = [['Order ID', 'Customer', 'Email', 'Status', 'Total', 'Date']]
    for order in orders:
        email = getattr(order, 'user', 'N/A')  
        name = getattr(order, 'name', 'N/A') 
        status = getattr(order, 'status', 'N/A') 
        created_at = getattr(order, 'created_at', 'N/A') 
        data.append([
            str(order.order_number),
            name,
            email,
            status,
            f"{order.grand_total:.2f} Rs",
            created_at
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
    ]))

    # Add the title and table to the elements
    styles = getSampleStyleSheet()
    title = "Sales Report"
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 0.5 * inch))
    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))

    # Add totals to the PDF
    totals_title = "Totals"
    elements.append(Paragraph(totals_title, styles['Heading2']))
    
    totals_data = [
        ['Total Sales Count:', total_sales_count],
        ['Total Revenue:', f"{total_revenue:.2f} Rs"],
        ['Total Coupon Deduction:', f"{coupon_deduction:.2f} Rs"],
        ['Total Discount:', f"{total_discount:.2f} Rs"]
    ]
    
    totals_table = Table(totals_data)
    totals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
    ]))
    
    elements.append(totals_table)

    doc.build(elements)

    buffer.seek(0)
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'
    return response





import openpyxl
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta, datetime
from django.db.models import Sum
import pytz
def download_sales_report_excel(request):
    # Create a new workbook and select the active worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    # Get the current time in the Asia/Kolkata timezone
    now = timezone.now().astimezone(pytz.timezone('Asia/Kolkata'))

    time_filter = request.GET.get('filter', None)
    start_date_str = request.GET.get('start_date', None)
    end_date_str = request.GET.get('end_date', None)

    orders = Order.objects.all().order_by('-created_at')

    # Initialize totals
    total_sales_count = orders.count()
    total_revenue = orders.aggregate(total=Sum('grand_total'))['total'] or 0
    coupon_deduction = orders.aggregate(total=Sum('coupon_price'))['total'] or 0
    total_old_price = Product.objects.aggregate(total=Sum('old_price'))['total'] or 0
    total_new_price = Product.objects.aggregate(total=Sum('price'))['total'] or 0
    total_discount = total_old_price - total_new_price

    # Apply date filters
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            end_date = end_date + timedelta(days=1)
            orders = orders.filter(created_at__date__gte=start_date, created_at__date__lt=end_date)
        except ValueError:
            pass
    elif time_filter:
        # Define filtering logic based on time_filter
        if time_filter == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_week':
            start_date = now - timedelta(days=now.weekday() + 7)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_month':
            start_date = now.replace(day=1) - timedelta(days=1)
            start_date = start_date.replace(day=1)
            orders = orders.filter(created_at__gte=start_date)
        elif time_filter == 'last_year':
            start_date = now.replace(month=1, day=1) - timedelta(days=1)
            start_date = start_date.replace(month=1, day=1)
            orders = orders.filter(created_at__gte=start_date)

    # Write headers to the Excel file
    headers = ['Order ID', 'Customer Name', 'Email', 'Status', 'Total', 'Payment Method', 'Date']
    ws.append(headers)

    # Write data to the Excel file
    for order in orders:
        customer = order.user  # Fetch the User instance
        name = getattr(customer, 'get_full_name', lambda: 'N/A')() if customer else 'N/A'  # Use get_full_name if available
        email = getattr(customer, 'email', 'N/A') if customer else 'N/A'  # Fetch email
        status = getattr(order, 'status', 'N/A')
        payment_method = getattr(order, 'payment_method', 'N/A')  # Assuming payment_method is a field in your Order model
        created_at = getattr(order, 'created_at', 'N/A')
        
        ws.append([
            str(order.order_number),
            name,
            email,
            status,
            f"{order.grand_total:.2f} Rs",
            payment_method,
            created_at.strftime('%Y-%m-%d')  # Format the date as needed
        ])

    # Append totals at the end of the data
    ws.append(['Total Orders:', total_sales_count, '', '', '', ''])
    ws.append(['Total Revenue:', f"{total_revenue:.2f} Rs", '', '', '', ''])
    ws.append(['Coupon Deduction:', f"{coupon_deduction:.2f} Rs", '', '', '', ''])
    ws.append(['Total Discount:', f"{total_discount:.2f} Rs", '', '', '', ''])

    # Set the HTTP response with the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'
    
    # Save the workbook to the response
    wb.save(response)
    
    return response


# def adminproducts(request):
#     products = Product.objects.all()  # Fetch all products
#     context = {
#         'products': products,
#     }
#     return render(request, 'admins/products.html', context)
@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def adminproducts(request):
    # Fetch all products
    products_list = Product.objects.all()

    # Calculate total stock for each product
    for product in products_list:
        product.stock = product.stock_small + product.stock_medium + product.stock_large

    # Create a Paginator object, showing 10 products per page
    paginator = Paginator(products_list, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    
    # Get the corresponding page of products
    products = paginator.get_page(page_number)

    context = {
        'products': products,
    }
    return render(request, 'admins/products.html', context)



@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def adminusers(request):
    # Fetch all users who are not admin, staff, superadmin, or superuser
    users_list = Account.objects.filter(is_admin=False, is_staff=False, is_superadmin=False, is_superuser=False)
    # Create a Paginator object with 10 users per page
    paginator = Paginator(users_list, 10)  # Show 10 users per page
    
    # Get the page number from the request query parameter
    page_number = request.GET.get('page')
    
    # Get the corresponding page of users
    users = paginator.get_page(page_number)
    context = {
        'users': users,
    }
    return render(request, 'admins/users.html', context)


@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def admincategories(request):
    categories = Category.objects.all().order_by('-id')  # Retrieve all categories, ordered by id descending
    
    paginator = Paginator(categories, 10)  # Show 10 categories per page
    page = request.GET.get('page')
    
    try:
        categories_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        categories_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        categories_page = paginator.page(paginator.num_pages)
    
    context = {
        'categories': categories_page
    }
    return render(request, 'admins/categories.html', context)



def toggle_category_status(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    if category.is_available == True:
        category.is_available = False
        messages.success(request, f'{category.category_name} has been marked as Unavailable.', extra_tags='error')
    else:
        category.is_available = True
        messages.success(request, f'{category.category_name} has been marked as Available.', extra_tags='success')
    
    category.save()
    return redirect('admincategories')

# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def adminaddcat(request):

#     if request.method == 'POST':
#         name = request.POST.get('name')
#         description = request.POST.get('description')
    

#         # Validate form data if needed
#         if name and description:
#             slug = slugify(name)
#             category = Category(
#                 category_name=name,
#                 description=description,
#                 slug=slug,
#             )
#             category.save()

#             return redirect('admincategories')
#     else:
#         # Handle the case where form data is missing
#         messages.error(request, 'All fields are required.')
#         return render(request, 'admins/categories.html')

#     return render(request, 'admins/categories.html')

@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def adminaddcat(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        if name and description:
            slug = slugify(name)
            if Category.objects.filter(category_name=name).exists():
                messages.error(request, 'Category already exists.', extra_tags='error')
            else:
                category = Category(
                    category_name=name,
                    description=description,
                    slug=slug,
                )
                category.save()
                messages.success(request, 'Category added successfully.', extra_tags='success')
                return redirect('admincategories')
        else:
            messages.error(request, 'All fields are required.', extra_tags='error')
    categories = Category.objects.order_by('-id')
    context = {
        'categories': categories,
    }
    return render(request, 'admins/categories.html', context)



@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def adminaddproduct(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        old_price = int(request.POST.get('old_price'))
        discount_percentage = int(request.POST.get('discount_percentage', 0))
        category_id = request.POST.get('category')
        stock_small = int(request.POST.get('stock_small', 0))
        stock_medium = int(request.POST.get('stock_medium', 0))
        stock_large = int(request.POST.get('stock_large', 0))

        # Process images
        images = request.FILES.get('images')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')


        # Find or create category
        category = Category.objects.get(id=category_id)
        slug = slugify(title)
        # Create and save the product
        # Check if product already exists in the specified category
        if Product.objects.filter(product_name=title, category=category).exists():
            messages.error(request, 'A product with this title already exists in the selected category.')
            return render(request, 'admins/addproduct.html', {'categories': Category.objects.all(), 'title': title, 'description': description, 'old_price': old_price, 'discount_percentage': discount_percentage, 'stock_small': stock_small, 'stock_medium': stock_medium, 'stock_large': stock_large})
        product = Product(
            product_name=title,
            description=description,
            old_price=old_price,
            discount_percentage=discount_percentage,
            category=category,
            stock_small=stock_small,
            stock_medium=stock_medium,
            stock_large=stock_large,
            slug=slug,
            images=images,
            image1=image1,
            image2=image2
        )
        product.applied_offer_name = 'Product Offer'
        product.save()

        return redirect('adminproducts')

    categories = Category.objects.all()
    return render(request, 'admins/addproduct.html', {'categories': categories})
from django.db import IntegrityError
@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def admineditproduct(request, product_id):
    product = Product.objects.get(id=product_id)  # Retrieve the existing product

    if request.method == 'POST':
        # Update product details
        new_discount_percentage = int(request.POST.get('discount_percentage', 0))

        # Check if the applied_offer_percentage exists and if the new discount is valid
        if product.applied_offer_percentage is not None:
            if new_discount_percentage < product.applied_offer_percentage:
                messages.error(request, 'Please ensure the discount percentage is higher than the current applied offer percentage.')
                return redirect('admineditproducts', product_id=product_id)
            elif new_discount_percentage > product.applied_offer_percentage:
                # Update applied_offer_name to "Default Product Offer" when a higher discount is applied
               
                product.applied_offer_name = 'Product Offer'
                product.product_disc_added = True

        product.product_name = request.POST.get('product_name')
        product.description = request.POST.get('description')
        product.old_price = int(request.POST.get('old_price'))
        product.discount_percentage = new_discount_percentage   
        product.category = Category.objects.get(id=request.POST.get('category'))
        product.stock_small = int(request.POST.get('stock_small', 0))
        product.stock_medium = int(request.POST.get('stock_medium', 0))
        product.stock_large = int(request.POST.get('stock_large', 0))

        # Process images
        images = request.FILES.get('images')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')

        if images:
            product.images = images
        if image1:
            product.image1 = image1
        if image2:
            product.image2 = image2

        product.slug = slugify(product.product_name)
        # Attempt to save the product
        try:
            product.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('adminproducts')
        except IntegrityError:
            messages.error(request, 'Failed to update product. A product with this name already exists.')
            return render(request, 'admins/editproduct.html', {
                'product': product,
                'categories': Category.objects.all(),
            })


        messages.success(request, 'Product updated successfully.')
        return redirect('adminproducts')

    categories = Category.objects.all()
    return render(request, 'admins/editproduct.html', {
        'product': product,
        'categories': categories
    })

# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def admineditproduct(request, product_id):
#     product = Product.objects.get(id=product_id)  # Retrieve the existing product

#     if request.method == 'POST':
#         # Update product details
#         product.product_name = request.POST.get('product_name')
#         product.description = request.POST.get('description')
#         product.old_price = int(request.POST.get('old_price'))
#         product.discount_percentage = int(request.POST.get('discount_percentage', 0))
#         product.category = Category.objects.get(id=request.POST.get('category'))
#         product.stock_small = int(request.POST.get('stock_small', 0))
#         product.stock_medium = int(request.POST.get('stock_medium', 0))
#         product.stock_large = int(request.POST.get('stock_large', 0))

#         # Process images
#         images = request.FILES.get('images')
#         image1 = request.FILES.get('image1')
#         image2 = request.FILES.get('image2')

#         if images:
#             product.images = images
#         if image1:
#             product.image1 = image1
#         if image2:
#             product.image2 = image2

#         product.slug = slugify(product.product_name)
#         product.save()

#         return redirect('adminproducts')

#     categories = Category.objects.all()
#     return render(request, 'admins/editproduct.html', {
#         'product': product,
#         'categories': categories
#     })




def toggle_product_status(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if product.is_available:
        product.is_available = False
        
        messages.success(request, f'{product.product_name} has been marked as Unavailable.')
    else:
        product.is_available = True
        # Assuming you want to restore stock counts or some default value when making the product available again.
        # Adjust the stock value as needed.
        messages.success(request, f'{product.product_name} has been marked as Available.')

    product.save()
    return redirect('adminproducts')


@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def admineditcat(request, category_id):
    # Retrieve the category to edit
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        # Validate form data if needed
        if name and description:
            # Check if a category with the same name already exists (excluding the current category)
            if Category.objects.filter(category_name=name).exclude(id=category_id).exists():
                messages.error(request, 'Category with this name already exists.')
            else:
                # Update category if the name is unique
                category.category_name = name
                category.description = description
                category.save()

                messages.success(request, 'Category updated successfully.')
                return redirect('admincategories')
        else:
            # Handle the case where form data is missing
            messages.error(request, 'All fields are required.')
    
    # If GET request or form is invalid, render the edit form with current data
    return render(request, 'admins/editcat.html', {'category': category})

# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def admineditcat(request, category_id):
    

#     # Retrieve the category to edit
#     category = get_object_or_404(Category, id=category_id)

#     if request.method == 'POST':
#         name = request.POST.get('name')
#         description = request.POST.get('description')
        
#         # Validate form data if needed
#         if name and description:
#             category.category_name = name
#             category.description = description
#             category.save()

#             messages.success(request, 'Category updated successfully.')
#             return redirect('admincategories')
#         else:
#             # Handle the case where form data is missing
#             messages.error(request, 'All fields are required.')
    
#     # If GET request or form is invalid, render the edit form with current data
#     return render(request, 'admins/editcat.html', {'category': category})

def toggle_user_status(request, user_id):
    user = get_object_or_404(Account, id=user_id)
    user.is_blocked = not user.is_blocked  # Toggle the is_active field
    user.save()
    if request.user == user:
        auth_logout(request)
    if user.is_blocked:
        messages.success(request, f'{user.username} is now Unblocked.')
    else:
        messages.success(request, f'{user.username} is now Blocked.')
    
    return redirect('adminusers')


def admin_logout(request):
    logout(request)
    return redirect('adminlogin')  # Redirect to the admin login page
@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def order_list(request):
    # Orders are fetched in the order they were created (by default)
    orders_list = Order.objects.all().order_by('-created_at')
    status_choices = Order.STATUS_CHOICES  # Get the status choices from the model

    # Filter out 'Cancelled' status
    # filtered_status_choices = [choice for choice in status_choices if choice[0] != 'Cancelled']
    filtered_status_choices = [
        choice for choice in status_choices 
        if choice[0] not in ['Cancelled', 'Return Request']
    ]
    paginator = Paginator(orders_list, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    orders = paginator.get_page(page_number)
    return render(request, 'admins/order_list.html', {
        'orders': orders,
        'status_choices': filtered_status_choices
    })
from orders.models import Wallet, WalletTransaction
from decimal import Decimal

def change_order_status(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status:
            order.status = new_status
            
            # Check if the new status is 'Return Success'
            if new_status == 'Return Success':
                wallet, created = Wallet.objects.get_or_create(user=order.user)
                wallet.update_balance('credit', Decimal(str(order.grand_total)))
                
                # Create a new wallet transaction record
                WalletTransaction.objects.create(
                    wallet=wallet,
                    amount=Decimal(str(order.grand_total)),
                    transaction_type='credit',
                    description=f'Refund for returned order #{order.id}'
                )
               

            order.save()
            messages.success(request, 'Order status updated successfully.')
        else:
            messages.error(request, 'Invalid status selected.')
        
    return redirect('order_list')  # Redirect to the page displaying orders

# def change_order_status(request, order_id):
#     if request.method == 'POST':
#         order = get_object_or_404(Order, id=order_id)
#         new_status = request.POST.get('status')
        
#         if new_status:
#             order.status = new_status
#             order.save()
#             messages.success(request, 'Order status updated successfully.')
#         else:
#             messages.error(request, 'Invalid status selected.')
        
#     return redirect('order_list')  # Redirect to the page displaying orders

def change_order_status_view(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        if new_status:
            order.status = new_status
            order.save()
            messages.success(request, 'Order status updated successfully.')
        else:
            messages.error(request, 'Invalid status selected.')
        
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))  


from django import template
import re

register = template.Library()

@register.filter
def slugify(value):
    return re.sub(r'[-\s]+', '-', value).lower()





from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def admincoupons(request):
    query = request.GET.get('search', '')
    if query:
        coupons = Coupon.objects.filter(
            Q(code__icontains=query) |
            Q(description__icontains=query)
        ).order_by('-id')
    else:
        coupons = Coupon.objects.all().order_by('-id')

    paginator = Paginator(coupons, 5)  # Show 10 coupons per page
    page = request.GET.get('page')
    try:
        coupons_page = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        coupons_page = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        coupons_page = paginator.page(paginator.num_pages)

    return render(request, 'admins/coupons.html', {'coupons': coupons_page})



# def edit_coupon(request, coupon_id):
#     coupon = get_object_or_404(Coupon, id=coupon_id)

#     if request.method == 'POST':
#         # Get the values from the form
#         coupon.code = request.POST.get('code')
#         coupon.description = request.POST.get('description')
#         coupon.discount_percentage = request.POST.get('discountPercentage')
#         coupon.minimum_purchase_amount = request.POST.get('minPurchaseAmount')
#         coupon.max_redeemable_value = request.POST.get('maxRedeemableValue')
#         coupon.quantity = request.POST.get('quantity')
#         coupon.expiry_date = request.POST.get('expiryDate')

#         # Save the updated coupon
#         coupon.save()

#         # Redirect to some page (e.g., a list of coupons)
#         return redirect('admincoupons')  # Replace with your actual redirect URL

#     # If GET request, pre-fill the form with current coupon data
#     return render(request, 'admins/editcoupon.html', {'coupon': coupon})

def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)

    if request.method == 'POST':
        # Get the values from the form
        new_code = request.POST.get('code')
        coupon.description = request.POST.get('description')
        coupon.discount_percentage = request.POST.get('discountPercentage')
        coupon.minimum_purchase_amount = request.POST.get('minPurchaseAmount')
        coupon.max_redeemable_value = request.POST.get('maxRedeemableValue')
        coupon.quantity = request.POST.get('quantity')
        coupon.expiry_date = request.POST.get('expiryDate')

        # Check if the new coupon code already exists (excluding the current coupon)
        if Coupon.objects.exclude(id=coupon_id).filter(code=new_code).exists():
            messages.error(request, 'A coupon with this code already exists. Please enter a different code.')
            return render(request, 'admins/editcoupon.html', {'coupon': coupon})  # Render the form again with the existing coupon

        # Save the updated coupon
        coupon.code = new_code
        coupon.save()

        # Show success message and redirect to the list of coupons
        messages.success(request, 'Coupon updated successfully.')
        return redirect('admincoupons')  # Replace with your actual redirect URL

    # If GET request, pre-fill the form with current coupon data
    return render(request, 'admins/editcoupon.html', {'coupon': coupon})




@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def adminoffers(request):
    # Query all Offer objects and order by created_at in descending order
    offers_list = Offer.objects.all().order_by('-created_at')
    
    # Create a Paginator object with 10 offers per page
    paginator = Paginator(offers_list, 10)  # Show 10 offers per page
    
    # Get the page number from the request query parameter
    page_number = request.GET.get('page')
    
    # Get the corresponding page of offers
    offers = paginator.get_page(page_number)
    
    # Pass offers and pagination object to the template context
    return render(request, 'admins/offers.html', {'offers': offers})

# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def add_product_offer(request):
#     if request.method == 'POST':
#         offer_name = request.POST.get('offer_name')
#         description = request.POST.get('description')
#         offer_percentage = request.POST.get('offer_percentage')
        
#         # You can add any additional validation here if needed
        
#         # Create the Offer object
#         offer = Offer(
#             offer_name=offer_name,
#             description=description,
#             offer_percentage=offer_percentage,
#             offer_type='product',  # Fixed as 'product'
#         )
#         messages.success(request, 'Product offer added successfully.')
#         offer.save()
        
#         return redirect('adminoffers')  # Redirect to a success page or wherever you want
    
#     return render(request, 'admins/add_product_offer.html')

@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def add_product_offer(request):
    if request.method == 'POST':
        offer_name = request.POST.get('offer_name')
        description = request.POST.get('description')
        offer_percentage = request.POST.get('offer_percentage')
        
        # Check if an offer with the same name already exists
        if Offer.objects.filter(offer_name=offer_name).exists():
            messages.error(request, 'An offer with this name already exists. Please choose a different name.')
            return render(request, 'admins/add_product_offer.html')  # Render the form again with the error message

        # Create the Offer object
        offer = Offer(
            offer_name=offer_name,
            description=description,
            offer_percentage=offer_percentage,
            offer_type='product',  # Fixed as 'product'
        )
        offer.save()  # Save the offer to the database
        messages.success(request, 'Product offer added successfully.')
        
        return redirect('adminoffers')  # Redirect to a success page or wherever you want
    
    return render(request, 'admins/add_product_offer.html')  # Render the form for GET requests

@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def add_cat_offer(request):
    if request.method == 'POST':
        offer_name = request.POST.get('offer_name')
        description = request.POST.get('description')
        offer_percentage = request.POST.get('offer_percentage')
        
        # Check if an offer with the same name already exists
        if Offer.objects.filter(offer_name=offer_name).exists():
            messages.error(request, 'An offer with this name already exists. Please choose a different name.')
            return render(request, 'admins/add_cat_offer.html')  # Render the form again with the error message

        # Create the Offer object
        offer = Offer(
            offer_name=offer_name,
            description=description,
            offer_percentage=offer_percentage,
            offer_type='category',  # Fixed as 'category'
        )
        offer.save()  # Save the offer to the database
        messages.success(request, 'Category offer added successfully.')
        
        return redirect('adminoffers')  # Redirect to a success page or wherever you want
    
    return render(request, 'admins/add_cat_offer.html')  # Render the form for GET requests

# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def add_cat_offer(request):
#     if request.method == 'POST':
#         offer_name = request.POST.get('offer_name')
#         description = request.POST.get('description')
#         offer_percentage = request.POST.get('offer_percentage')
        
#         # You can add any additional validation here if needed
        
#         # Create the Offer object
#         offer = Offer(
#             offer_name=offer_name,
#             description=description,
#             offer_percentage=offer_percentage,
#             offer_type='category',  # Fixed as 'product'
#         )
#         messages.success(request, 'Category offer added successfully.')
#         offer.save()
        
#         return redirect('adminoffers')  # Redirect to a success page or wherever you want
    
#     return render(request, 'admins/add_cat_offer.html')

@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def edit_product_offer(request, id):
    offer = get_object_or_404(Offer, id=id)

    if request.method == 'POST':
        offer_name = request.POST.get('offer_name').strip()
        description = request.POST.get('description').strip()
        offer_percentage = request.POST.get('offer_percentage').strip()

        # Check if the new offer name already exists (excluding the current offer)
        if Offer.objects.exclude(id=id).filter(offer_name=offer_name).exists():
            messages.error(request, 'An offer with this name already exists. Please choose a different name.')
            return redirect('edit_product_offer', id=id)  # Redirect back to the edit page with the same ID

        # Update the offer details
        offer.offer_name = offer_name
        offer.description = description
        offer.offer_percentage = offer_percentage
        
        try:
            offer.save()
            messages.success(request, 'Offer details updated successfully.')
            return redirect('adminoffers')
        except IntegrityError:
            messages.error(request, 'An error occurred while saving the offer. Please try again.')
            return redirect('edit_product_offer', id=id)

    context = {
        'offer': offer
    }
    return render(request, 'admins/edit_product_offer.html', context)

@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def edit_cat_offer(request, id):
    offer = get_object_or_404(Offer, id=id)

    if request.method == 'POST':
        offer_name = request.POST.get('offer_name').strip()
        description = request.POST.get('description').strip()
        offer_percentage = request.POST.get('offer_percentage').strip()

        # Check if the new offer name already exists (excluding the current offer)
        if Offer.objects.exclude(id=id).filter(offer_name=offer_name).exists():
            messages.error(request, 'An offer with this name already exists. Please choose a different name.')
            return redirect('edit_cat_offer', id=id)  # Redirect back to the edit page with the same ID

        # Update the offer details
        offer.offer_name = offer_name
        offer.description = description
        offer.offer_percentage = offer_percentage
        
        try:
            offer.save()
            messages.success(request, 'Category offer details updated successfully.')
            return redirect('adminoffers')
        except IntegrityError:
            messages.error(request, 'An error occurred while saving the category offer. Please try again.')
            return redirect('edit_cat_offer', id=id)

    context = {
        'offer': offer
    }
    return render(request, 'admins/edit_cat_offer.html', context)

@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def edit_offer(request, id):
    offer = get_object_or_404(Offer, id=id)

    if request.method == 'POST':
        offer_name = request.POST.get('offer_name').strip()
        description = request.POST.get('description').strip()
        offer_percentage = request.POST.get('offer_percentage').strip()

        # Check if the new offer name already exists (excluding the current offer)
        if Offer.objects.exclude(id=id).filter(offer_name=offer_name).exists():
            messages.error(request, 'An offer with this name already exists. Please choose a different name.')
            return redirect('edit_offer', id=id)  # Redirect back to the edit page with the same ID

        # Update the offer details
        offer.offer_name = offer_name
        offer.description = description
        offer.offer_percentage = offer_percentage
        
        try:
            offer.save()
            if offer.offer_type == 'product':
                messages.success(request, 'Product offer details updated successfully.')
            else:
                messages.success(request, 'Category offer details updated successfully.')
            return redirect('adminoffers')
        except IntegrityError:
            messages.error(request, 'An error occurred while saving the offer. Please try again.')
            return redirect('edit_offer', id=id)

    context = {
        'offer': offer
    }

    # Dynamically render template based on the offer_type
    if offer.offer_type == 'product':
        return render(request, 'admins/edit_product_offer.html', context)
    else:
        return render(request, 'admins/edit_cat_offer.html', context)

# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def edit_product_offer(request, id):
#     offer = get_object_or_404(Offer, id=id)

#     if request.method == 'POST':
#         offer_name = request.POST.get('offer_name').strip()
#         description = request.POST.get('description').strip()
#         offer_percentage = request.POST.get('offer_percentage').strip()

#         # Check if the new offer name already exists (excluding the current offer)
#         if Offer.objects.exclude(id=id).filter(offer_name=offer_name).exists():
#             messages.error(request, 'An offer with this name already exists. Please choose a different name.')
#             return redirect('edit_product_offer', id=id)  # Redirect back to the edit page with the same ID

#         # Update the offer details
#         offer.offer_name = offer_name
#         offer.description = description
#         offer.offer_percentage = offer_percentage
#         try:
#             offer.save()
#             messages.success(request, 'Offer details updated successfully.')
#             return redirect('adminoffers')
#         except IntegrityError:
#             messages.error(request, 'An error occurred while saving the offer. Please try again.')
#             return redirect('edit_product_offer', id=id)

#     context = {
#         'offer': offer
#     }
#     return render(request, 'admins/edit_product_offer.html', context)

# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def edit_cat_offer(request, id):
#     offer = get_object_or_404(Offer, id=id)

#     if request.method == 'POST':
#         offer_name = request.POST.get('offer_name')
#         description = request.POST.get('description')
#         offer_percentage = request.POST.get('offer_percentage')

#         # Check if the new offer name already exists (excluding the current offer)
#         if Offer.objects.exclude(id=id).filter(offer_name=offer_name).exists():
#             messages.error(request, 'An offer with this name already exists. Please choose a different name.')
#             return redirect('edit_cat_offer', id=id)  # Redirect back to the edit page with the same ID

#         # Update the offer details
#         offer.offer_name = offer_name
#         offer.description = description
#         offer.offer_percentage = offer_percentage
#         offer.save()
        
#         messages.success(request, 'Category offer details updated successfully.')
#         return redirect('adminoffers')

#     context = {
#         'offer': offer
#     }
#     return render(request, 'admins/edit_cat_offer.html', context)


# @user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
# def edit_offer(request, id):
#     offer = get_object_or_404(Offer, id=id)

#     if request.method == 'POST':
#         offer_name = request.POST.get('offer_name')
#         description = request.POST.get('description')
#         offer_percentage = request.POST.get('offer_percentage')

#         offer.offer_name = offer_name
#         offer.description = description
#         offer.offer_percentage = offer_percentage
#         offer.save()
        
#         if offer.offer_type == 'product':
#             messages.success(request, 'Product offer details updated successfully.')
#         else:
#             messages.success(request, 'Category offer details updated successfully.')
        
#         return redirect('adminoffers')

#     context = {
#         'offer': offer
#     }

#     # Dynamically render template based on the offer_type
#     if offer.offer_type == 'product':
#         return render(request, 'admins/edit_product_offer.html', context)
#     else:
#         return render(request, 'admins/edit_cat_offer.html', context)


def toggle_offer_status(request, id):
    offer = get_object_or_404(Offer, id=id)
    if offer.status == 'active':
        offer.status = 'inactive'
        offer.action = 'block'
        messages.success(request, 'The offer has been blocked successfully.')
    else:
        offer.status = 'active'
        offer.action = 'unblock'
        messages.success(request, 'The offer has been unblocked successfully.')
    offer.save()
    return redirect('adminoffers')

@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def show_items(request):
    view = request.POST.get('view')
    offer_id = request.POST.get('offer_id')
    print(offer_id)
    if view == 'products':
        items = Product.objects.all().order_by('-created_date')
        template_name = 'admins/products_list_off.html'
    elif view == 'categories':
        items = Category.objects.all()
        template_name = 'admins/categories_list_off.html'
    else:
        items = []
        template_name = 'admins/error.html'  # Or any error handling template

    return render(request, template_name, {'products': items, 'selected_offer_id': offer_id})




# def apply_offer_to_product(request):
#     if request.method == 'POST':
#         product_id = request.POST.get('product_id')
#         offer_id = request.POST.get('offer_id')
#         # print(product_id, offer_id)
#         product = get_object_or_404(Product, id=product_id)
#         offer = get_object_or_404(Offer, id=offer_id)
        
#         # Apply the offer to the product
#         product.discount_percentage = offer.offer_percentage
#         product.product_disc_added=True
#         product.save()
#         messages.success(request, 'Offer applied successfully.')
#         return redirect('adminoffers')  # Redirect to a success page or back to the product list
#     else:
#         return redirect('adminoffers')  # Handle cases where the request method is not POST


def apply_offer_to_product(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        offer_id = request.POST.get('offer_id')

        # Retrieve the product and offer
        product = get_object_or_404(Product, id=product_id)
        offer = get_object_or_404(Offer, id=offer_id)

        # Check the existing discount
        existing_discount = product.discount_percentage

        # Apply the higher discount percentage
        if offer.offer_percentage > existing_discount:
            product.discount_percentage = offer.offer_percentage
            product.product_disc_added = True
            product.applied_offer_name = offer.offer_name
            product.applied_offer_percentage = offer.offer_percentage
            product.save()
            messages.success(request, 'Offer applied successfully to the product.')
        else:
            messages.warning(request, 'The existing discount is higher than the offer.')

        return redirect('adminoffers')  # Redirect to a success page or back to the product list
    else:
        return redirect('adminoffers')  # Handle cases where the request method is not POST



def remove_offer_from_product(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        offer_id = request.POST.get('offer_id')
        # print(product_id, offer_id)
        product = get_object_or_404(Product, id=product_id)
        offer = get_object_or_404(Offer, id=offer_id)
        
        # Apply the offer to the product
        product.discount_percentage = 0
        product.product_disc_added=False
        product.applied_offer_name = 'No offer Applied'
        product.applied_offer_percentage = 0
        
        product.save()
        messages.success(request, 'Offer removed successfully.')
    return redirect('adminoffers')

def apply_offer_to_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        offer_id = request.POST.get('offer_id')

        # Retrieve the category and offer
        category = get_object_or_404(Category, id=category_id)
        offer = get_object_or_404(Offer, id=offer_id)

        # Retrieve all products in the specified category
        products = Product.objects.filter(category=category)

        # Update each product's discount percentage
        for product in products:
            existing_discount = product.discount_percentage

            # Apply the higher discount percentage
            if offer.offer_percentage > existing_discount:
                product.discount_percentage = offer.offer_percentage
                product.cat_disc_added = True
                product.product_disc_added = True
                product.applied_offer_name = 'Cat Off :' + offer.offer_name
                product.save()
        
        # Success message for the category
        category.offer_added = True
        category.applied_offer = offer  # Update this line
        category.applied_offer_name = offer.offer_name
        category.applied_offer_percentage = offer.offer_percentage
        category.save()
        
        messages.success(request, 'Offer applied successfully to all products in the category.')

        return redirect('adminoffers')  # Redirect to a success page or back to the product list

    else:
        return redirect('adminoffers')  # Handle cases where the request method is not POST 


# def remove_offer_from_category(request):
#     if request.method == 'POST':
#         category_id = request.POST.get('category_id')
#         offer_id = request.POST.get('offer_id')
        
#         # Retrieve category and offer
#         category = get_object_or_404(Category, id=category_id)
#         offer = get_object_or_404(Offer, id=offer_id)
        
#         # Retrieve all products in the specified category
#         products = Product.objects.filter(category=category)
        

#         # Update each product's discount percentage
#         for product in products:
#             product.discount_percentage = 0
#             product.cat_disc_added = False
#             product.product_disc_added=False
#             product.save()
        
#         # Success message
#         category.offer_added=False
#         category.save()
#         messages.success(request, 'Offer applied successfully.')
        
#         return redirect('adminoffers')  # Redirect to a success page or back to the product list
    
#     else:
#         return redirect('adminoffers')
def remove_offer_from_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        offer_id = request.POST.get('offer_id')
        
        # Retrieve category and offer
        category = get_object_or_404(Category, id=category_id)
        offer = get_object_or_404(Offer, id=offer_id)
        
        # Retrieve all products in the specified category
        products = Product.objects.filter(category=category)
        
        # Update each product's discount flags
        for product in products:
            # Check if the product's applied_offer_name matches the category offer
            if product.applied_offer_name == f'Cat Off :{offer.offer_name}':
                product.cat_disc_added = False
                product.product_disc_added = False
                product.applied_offer_name = None  # Remove the applied offer name if necessary
                product.applied_offer_name = 'No Offer Applied'
                product.discount_percentage = 0
                product.applied_offer_percentage = 0
                # Optionally, reset discount_percentage to its original value or leave it unchanged
                # product.discount_percentage = original_value  # Uncomment if you have a way to track the original value
                product.save()
        
        # Success message
        category.offer_added = False
        category.applied_offer = None  # Clear the applied offer reference
        category.applied_offer_name = None
        category.applied_offer_percentage = 0  # Reset to zero if required
        category.save()
        
        messages.success(request, 'Offer removed successfully from all products in the category.')
        
        return redirect('adminoffers')  # Redirect to a success page or back to the product list
    
    else:
        return redirect('adminoffers')  # Handle cases where the request method is not POST 


# from orders.models import OrderedItems
# def order_detail_view(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     STATUS_CHOICES = Order.STATUS_CHOICES  # Assuming STATUS_CHOICES is defined in your Order model
#     ordered_items = OrderedItems.objects.filter(order_number=order.order_number)
#     print(ordered_items)
#     return render(request, 'admins/order_detail_view.html',  {'order': order, 'status_choices': STATUS_CHOICES, 'ordered_items': ordered_items,})
from accounts.models import Address
from django.shortcuts import get_object_or_404, render
from orders.models import OrderedItems, Order
from django.db.models import Sum, F
@user_passes_test(admin_required, login_url=reverse_lazy('adminlogin'))
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    STATUS_CHOICES = Order.STATUS_CHOICES
    
    ordered_items = OrderedItems.objects.filter(order_number=order.order_number)
    checked_address = Address.objects.filter(user=request.user, checked=True).first()
    print("This is is check address yoo", checked_address)
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
    
    return render(request, 'admins/order_detail_view.html', {
        'order': order,
        'status_choices': STATUS_CHOICES,
        'aggregated_items': aggregated_items,
        'checked_address': checked_address
    })
