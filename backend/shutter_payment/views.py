from django.conf import settings
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .models import Order,PhotoPackage
import razorpay

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
def home(request):
    return render(request,"Home-Page/Home.html")

def products(request):
    products= PhotoPackage.objects.all()
    return render(request,"Home-Page/products.html",{'products':products})

def error(request):
    return render(request,"razorpay/error.html")

def create_order(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        number_of_copies = int(request.POST.get('number_of_copies', 1))  # Get copies, default is 1
        
        # Ensure number_of_copies is within limits (1-3)
        if number_of_copies < 1:
            number_of_copies = 1
        elif number_of_copies > 3:
            number_of_copies = 3

        product = PhotoPackage.objects.get(id=product_id)

        # Adjust price based on number_of_copies
        price_multiplier = number_of_copies  # 1x, 2x, or 3x
        total_price = product.price * price_multiplier

        order_data = {
            'amount': int(total_price * 100),  # Convert to paise
            'currency': 'INR',
            'payment_capture': '1'
        }
        order = client.order.create(data=order_data)

        # ✅ Create Order in DB and store UUID
        new_order = Order.objects.create(
            razorpay_order_id=order["id"],
            total_amount=total_price,
            number_of_copies=number_of_copies  # Store the selected copies
        )

        return render(request, 'razorpay/payment.html', {
            'uuid': new_order.id,  
            'order_id': order['id'],  
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'product_name': product.name,
            'price': total_price  # Show correct total price
        })


@csrf_exempt
def razorpay_webhook(request):
    if request.method == 'POST':
        payload = request.body.decode('utf-8')
        sig_header = request.META['HTTP_X_RAZORPAY_SIGNATURE']
        
        
        if verify_signature(payload, sig_header):
            event = json.loads(payload)
            
            if event['event'] == 'payment.captured':
                print("payment captured",event)
                payment_id = event['payload']['payment']['entity']['id']
                order_id = event['payload']['payment']['entity']['order_id']
                try:
                    order = Order.objects.get(razorpay_order_id=order_id)
                    order.razorpay_payment_id = payment_id
                    order.payment_verified = True
                    order.save()

                    return JsonResponse({'status': 'success', 'message': 'Payment captured successfully'})

                except Order.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Order not found'})

            elif event['event'] == 'payment.failed':
                print("payment failed")
                return JsonResponse({'status': 'error', 'message': 'Payment failed'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid signature'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def verify_signature(payload, sig_header):
    return client.utility.verify_webhook_signature(payload, sig_header, settings.WEBHOOK_SECRET)

def photo(request):
    return render(request,'photo/home_page.html')

def payment_status(request, order_id):
    try:
        order = Order.objects.get(razorpay_order_id=order_id)
        if order.payment_status:
            print("hey")
            return JsonResponse({'status': 'success'})

        else:
            return JsonResponse({'status': 'failed'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'failed', 'message': 'Order not found'})
    
from .models import Order, Photo

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def capture_photo(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        image_file = request.FILES.get('image')
        
        try:
            order = Order.objects.get(id=order_id)
            if order.photos.count() >= 4:
                return JsonResponse({'status': 'error', 'message': 'Photo limit reached'})

            Photo.objects.create(
                order=order,
                image_url=image_file
            )
            return JsonResponse({'status': 'success', 'photo_count': order.photos.count()})
            
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid order'})
    # Handle unsupported HTTP methods
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)
def photobooth_view(request, order_id):
    print(f"Received order_id: {order_id}")  # ✅ Debugging

    order = get_object_or_404(Order, id=order_id)  # Ensure this exists!
    return render(request, 'photo/photobooth.html', {'order': order})

# def photobooth_view(request):
#     # order = get_object_or_404(Order, id=order_id)
#     return render(request, 'photo/photobooth.html')    
