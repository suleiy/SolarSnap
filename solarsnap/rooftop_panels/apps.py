from django.apps import AppConfig
""" from flask import Flask, render_template, request
from PIL import Image
import numpy as np

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'GET':
        return render_template('index.html', msg='')

    image = request.files['file']
    img = Image.open(image)
    img = np.array(img)

    print(img)
    print(img.shape)

    return render_template('index.html', msg='Your image has been uploaded')

if __name__ == '__main__':
    app.run() """

class RooftopPanelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rooftop_panels'
