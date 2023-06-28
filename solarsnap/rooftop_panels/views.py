from django.http import HttpResponse
from django.shortcuts import render, redirect
from .update import *
from .forms import *
import time
import replicate

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
def index(request):
    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            time.sleep(3)
            if request.POST['submit'] == 'aerial':
                return redirect('successAerial')
            elif request.POST['submit'] == 'ground':
                return redirect('successGround')
    else:
        form = ImageForm()
    return render(request, 'index.html', {'form': form})

def successGround(request):
    latest_image = Image.objects.order_by('id').last()
    latest_image_url = latest_image.uploaded_image.url
    #return render(request, 'confirmation.html', {'latest_image_url': latest_image_url})
    output = replicate.run(
        "arielreplicate/instruct-pix2pix:10e63b0e6361eb23a0374f4d9ee145824d9d09f7a31dcd70803193ebc7121430",
        input={'input_image': open('../solarsnap/solarsnap'+ latest_image_url, 'rb'), 'instruction_text':"add solar panels to roof"}
    )
    return render(request, 'confirmation.html', {'latest_image_url': output})

def successAerial(request):
    latest_image = Image.objects.order_by('id').last()
    latest_image_url = latest_image.uploaded_image.url

    if request.method == 'POST':
        color=getColor(request.POST['submit'])
        
    color = "silver"
    pl, pw, l, w, solar_angle = 4, 1, 8, 5, 30
    image = cv2.imread('../solarsnap/solarsnap'+ latest_image_url) #input image path 
    img = cv2.pyrDown(image)
    print('image shape : ',img.shape)
    n_white_pix = np.sum(img==255)
    # Upscaling of Image
    high_reso_orig = cv2.pyrUp(image)
    high_reso_orig_withShape=high_reso_orig

    # White blank image for contours of Canny Edge Image
    canny_contours = white_image(image)
    # White blank image for contours of original image
    image_contours = white_image(image)

    # White blank images removing rooftop's obstruction
    image_polygons = grays(canny_contours)
    canny_polygons = grays(canny_contours)

    # Gray Image
    grayscale = grays(image)
   
    # Edge Sharpened Image
    sharp_image = sharp(grayscale)
    # Canny Edge
    edged = cv2.Canny(sharp_image, 180, 240)
    edge_image = sharp_image      
    # Otsu Threshold (Adaptive Threshold)
    # thresh = cv2.threshold(sharp_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    thresh = cv2.threshold(sharp_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # Contours in Original Image
    contours_img(cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2], image_contours,edged,image_polygons)
    # Contours in Canny Edge Image
    contours_canny(cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2], canny_contours, edged, canny_polygons)
    # Optimum place for placing Solar Panels
    solar_roof = cv2.bitwise_and(image_polygons, canny_polygons)
    #print('solar white pix : ',n_white_pix)
    print('size of solar roof : ',solar_roof.shape)
    new_image = white_image(image)
    ret, thresh2 = cv2.threshold(edge_image, 198, 255, cv2.THRESH_BINARY)
    n_white_pix = np.sum(thresh2==255)
    area_roof = n_white_pix*0.075
    print('area of building roof : ',n_white_pix*0.075,'sqm')
    print('new image shape',new_image.shape)
    # Rotation of Solar Panels
    panel_rotation(pl, solar_roof, color, new_image, high_reso_orig, l,w,pw,pl,solar_angle)
    return render(request, 'aerial.html')