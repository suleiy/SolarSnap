# Generated by Django 5.0.dev20230609101817 on 2023-06-23 14:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rooftop_panels', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='image',
            name='name',
            field=models.CharField(default='image', max_length=50),
            preserve_default=False,
        ),
    ]
