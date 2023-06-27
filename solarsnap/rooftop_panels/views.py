from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import *
import time
import replicate


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
    #return render(request, 'confirmation.html', {'latest_image_url': latest_image_url})
    output = replicate.run(
        "arielreplicate/instruct-pix2pix:10e63b0e6361eb23a0374f4d9ee145824d9d09f7a31dcd70803193ebc7121430",
        input={'input_image': open('../solarsnap/solarsnap'+ latest_image_url, 'rb'), 'instruction_text':"add solar panels to roof"}
    )
    return render(request, 'confirmation.html', {'latest_image_url': output})

