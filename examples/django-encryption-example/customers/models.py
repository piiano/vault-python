from django.db import models

from django_encryption.fields import EncryptedCharField, EncryptedEmailField, EncryptedDateField, EncryptionType


class Customer(models.Model):
    name = EncryptedCharField(data_type_name='NAME')
    email = EncryptedEmailField(data_type_name='EMAIL')
    phone = EncryptedCharField(data_type_name='PHONE_NUMBER')
    address = EncryptedCharField(
        encryption_type=EncryptionType.randomized, expiration_secs=10, data_type_name='ADDRESS')
    ssn = EncryptedCharField(
        encryption_type=EncryptionType.randomized, data_type_name='SSN')
    dob = EncryptedDateField(data_type_name='DATE_OF_BIRTH')
