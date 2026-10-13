from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
import logging

def page(request):
    return render(request, 'page.html')