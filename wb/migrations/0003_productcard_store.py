# Generated by Django 2.2 on 2021-04-28 14:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wb', '0002_auto_20210428_1331'),
    ]

    operations = [
        migrations.AddField(
            model_name='productcard',
            name='store',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='product_cards', to='wb.Store'),
        ),
    ]
