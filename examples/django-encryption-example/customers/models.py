from django.db import models

from django_encryption.fields import EncryptedCharField, EncryptedEmailField, EncryptedDateField, EncryptionType, EncryptingModel


class Customer(EncryptingModel):
    name = EncryptedCharField(data_type_name='NAME')
    email = EncryptedEmailField(data_type_name='EMAIL')
    phone = EncryptedCharField(
        data_type_name='PHONE_NUMBER', null=True, blank=True)
    ssn = EncryptedCharField(
        encryption_type=EncryptionType.randomized, data_type_name='SSN', null=True, blank=True)
    dob = EncryptedDateField(
        data_type_name='DATE_OF_BIRTH', null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
