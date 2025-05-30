# Generated by Django 5.2.1 on 2025-05-12 22:24

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='has_seats',
            field=models.BooleanField(default=False, verbose_name='¿Tiene asientos numerados?'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='entry_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Hora de entrada'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='exit_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Hora de salida'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='expiration_date',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de expiración'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='is_paid',
            field=models.BooleanField(default=False, verbose_name='Pagado'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='seat_number',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Número de asiento'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='section',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Sección'),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto')),
                ('payment_date', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de pago')),
                ('payment_method', models.CharField(max_length=50, verbose_name='Método de pago')),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('completed', 'Completado'), ('failed', 'Fallido')], default='pending', max_length=20, verbose_name='Estado')),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True, verbose_name='ID de transacción')),
                ('ticket', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='eventos.ticket', verbose_name='Entrada')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Usuario')),
            ],
            options={
                'verbose_name': 'Pago',
                'verbose_name_plural': 'Pagos',
            },
        ),
    ]
