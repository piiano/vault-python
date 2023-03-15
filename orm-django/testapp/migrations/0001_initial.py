from django.db import migrations, models

import piiano_django_encryption.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TestModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enc_char_field', piiano_django_encryption.fields.EncryptedCharField()),
                ('enc_text_field', piiano_django_encryption.fields.EncryptedTextField()),
                ('enc_date_field', piiano_django_encryption.fields.EncryptedDateField(null=True)),
                ('enc_date_now_field', piiano_django_encryption.fields.EncryptedDateField(auto_now=True, null=True)),
                ('enc_date_now_add_field', piiano_django_encryption.fields.EncryptedDateField(auto_now_add=True, null=True)),
                ('enc_datetime_field', piiano_django_encryption.fields.EncryptedDateTimeField(null=True)),
                ('enc_boolean_field', piiano_django_encryption.fields.EncryptedBooleanField(default=True)),
                ('enc_integer_field', piiano_django_encryption.fields.EncryptedIntegerField(null=True)),
                ('enc_positive_integer_field', piiano_django_encryption.fields.EncryptedPositiveIntegerField(null=True)),
                ('enc_small_integer_field', piiano_django_encryption.fields.EncryptedSmallIntegerField(null=True)),
                ('enc_positive_small_integer_field', piiano_django_encryption.fields.EncryptedPositiveSmallIntegerField(null=True)),
                ('enc_big_integer_field', piiano_django_encryption.fields.EncryptedBigIntegerField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
