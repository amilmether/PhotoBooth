from django.conf import settings
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .models import Order,PhotoPackage


def home(request):
    return render(request,"Home-Page/Home.html")

def products(request):
    products= PhotoPackage.objects.all()
    return render(request,"Home-Page/products.html",{'products':products})
