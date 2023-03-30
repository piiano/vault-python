import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vault_sample_django.settings")
django.setup()

from django_encryption.fields import VaultException, get_vault # noqa
from customers.models import Customer


"""
This example shows how to add a customer to the
database using the Django ORM (and not from the web interface).
"""


def main():
    customer = Customer()
    customer.name = 'John'
    customer.email = 'JohnA@gmail.com'
    customer.phone = '+972-54-1234567'
    customer.ssn = '078-05-1120'
    customer.dob = '2023-03-21'
    customer.state = 'IL'
    customer.save()


if __name__ == '__main__':
    main()
