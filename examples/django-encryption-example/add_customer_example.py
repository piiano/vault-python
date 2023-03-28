import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vault_sample_django.settings")

from django_encryption.fields import VaultException, get_vault # noqa
from customers.models import Customer


def main():
    customer = Customer()
    customer.name = 'John'
    customer.email = 'JohnA@gmail.com'
    customer.phone = '+972-54-1234567'
    customer.address = 'John street 1st'
    customer.ssn = '123-45-6789'
    customer.save()


if __name__ == '__main__':
    main()


