from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordering', '0005_finalize_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='customersession',
            name='customer_name',
            field=models.CharField(
                blank=True,
                max_length=100,
                help_text='Optional display name entered by the customer in the cart.',
            ),
        ),
    ]
