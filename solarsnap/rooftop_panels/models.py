from django.db import models
from datetime import datetime
# Create your models here.

class Image(models.Model):
    name = models.CharField(max_length=50)
    uploaded_image = models.ImageField(upload_to='images/')
    date_added = datetime.now()
