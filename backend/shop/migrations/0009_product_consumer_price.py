"""قیمت مصرف‌کننده + گزینهٔ نمایش آن (قیمت فروش به‌صورت «قیمت اختصاصی» زیر قیمت مصرف‌کنندهٔ خط‌خورده)"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0008_product_unit'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='consumer_price',
            field=models.BigIntegerField(default=0, help_text='قیمت رسمی بازار؛ ۰ = خاموش. روی سایت با خط خورده نمایش داده می‌شود',
                                         verbose_name='قیمت مصرف‌کننده (تومان)'),
        ),
        migrations.AddField(
            model_name='product',
            name='show_consumer_price',
            field=models.BooleanField(default=False, help_text='قیمت فروش به‌صورت «قیمت اختصاصی» زیر قیمت مصرف‌کنندهٔ خط‌خورده نمایش داده می‌شود',
                                      verbose_name='نمایش قیمت مصرف‌کننده'),
        ),
    ]
