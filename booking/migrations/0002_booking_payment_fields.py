from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("booking", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="booking",
            name="is_paid",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="booking",
            name="payment_reference",
            field=models.CharField(blank=True, max_length=40),
        ),
    ]
