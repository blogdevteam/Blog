# Generated by Django 2.2.2 on 2019-07-04 05:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogApp', '0007_auto_20190703_1905'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.CharField(default='https://raw.githubusercontent.com/oi-songer/oi-songer.github.io/master/portal.jpg', max_length=100, null=True),
        ),
    ]
