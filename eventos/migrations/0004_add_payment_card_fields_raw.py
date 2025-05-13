from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0003_ticket_scan_count'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE eventos_payment ADD COLUMN card_last_digits VARCHAR(4) NULL;",
            "ALTER TABLE eventos_payment DROP COLUMN card_last_digits;"
        ),
        migrations.RunSQL(
            "ALTER TABLE eventos_payment ADD COLUMN card_type VARCHAR(20) NULL;",
            "ALTER TABLE eventos_payment DROP COLUMN card_type;"
        ),
    ]