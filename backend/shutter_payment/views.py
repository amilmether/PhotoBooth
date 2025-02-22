from django.conf import settings
from django.shortcuts import render, redirect
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


def create_order(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = PhotoPackage.objects.get(id=product_id)
       
       
        order_data = {
            # 'amount': int(product.price * 100), 
            'amount': int(1 * 100),
            'currency': 'INR',
            'payment_capture': '1'
        }
        order = client.order.create(data=order_data)
        Order.objects.create(
            # user=request.user,
            # product=product,
            razorpay_order_id=order["id"],
            total_amount=product.price
        )
        return render(request, 'razorpay/payment.html', {
            'order_id': order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'product_name': product.name,
            'price': product.price / 100  
        })
    return redirect('photo/')  


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
            return JsonResponse({'status': 'success'})
        
        else:
            return JsonResponse({'status': 'failed'})
    except Order.DoesNotExist:
        return JsonResponse({'status': 'failed', 'message': 'Order not found'})
    
