# Generated by Django 4.1.7 on 2023-03-29 10:59

from django.db import migrations, models
import django_encryption.fields


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='address',
        ),
        migrations.AddField(
            model_name='customer',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='dob',
            field=django_encryption.fields.EncryptedDateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='phone',
            field=django_encryption.fields.EncryptedCharField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='customer',
            name='ssn',
            field=django_encryption.fields.EncryptedCharField(blank=True, null=True),
        ),
    ]
