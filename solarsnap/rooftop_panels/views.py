from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import *
import time


def index(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            time.sleep(3)
            return redirect('success')
    else:
        form = ImageForm()
    return render(request, 'index.html', {'form': form})

def success(request):
    latest_image = Image.objects.order_by('id').last()
    latest_image_url = latest_image.uploaded_image.url
    return render(request, 'confirmation.html', {'latest_image_url': latest_image_url})

