from django.db import models

from django_encryption.fields import EncryptedCharField, EncryptedEmailField, EncryptedDateField, EncryptionType, raise_error


class Customer(models.Model):
    name = EncryptedCharField()
    email = EncryptedEmailField()
    phone = EncryptedCharField()
    address = EncryptedCharField(
        encryption_type=EncryptionType.randomized, expiration_secs=10)
    ssn = EncryptedCharField(
        encryption_type=EncryptionType.randomized)
    dob = EncryptedDateField()
