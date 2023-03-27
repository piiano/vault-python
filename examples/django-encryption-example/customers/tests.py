from django.test import TestCase
from django_encryption.fields import get_vault, EncryptedMixin, VaultException, mask_field, transform
from customers.models import Customer
import datetime

# Create your tests here.
TEST_COLLECTION_NAME = "persons"

class TestCustomer(TestCase):
    def setUp(self) -> None:

        vault = get_vault()
        vault.add_collection(TEST_COLLECTION_NAME, 'PERSONS', [])
        try:
            for field in Customer._meta.get_fields():
                if not isinstance(field, EncryptedMixin):
                    continue
                vault.add_property(
                    property_name=field.vault_property,
                    collection=TEST_COLLECTION_NAME,
                    description='',
                    is_encrypted=True,
                    is_index=False,
                    is_nullable=True,
                    is_unique=False,
                    data_type_name=field.data_type_name,
                )
        except VaultException:
            vault.remove_collection(TEST_COLLECTION_NAME)

    def tearDown(self) -> None:
        vault = get_vault()
        vault.remove_collection(TEST_COLLECTION_NAME)
    def test_add_customer(self):
        self.add_customer()

        customers = list(Customer.objects.all())
        assert len(customers) == 1

        # Check that the data is returned as expected
        customer = customers[0]
        self.assertEqual(customer.name, 'John')
        self.assertEqual(customer.email, 'JohnA@gmail.com')
        self.assertEqual(customer.phone, '+972541234567')
        self.assertEqual(customer.address, 'Tel Aviv')
        self.assertEqual(customer.dob, datetime.date(1990, 1, 1))
        self.assertEqual(customer.ssn, '123-12-1234')

    def test_encrypted_fields(self):
        self.add_customer()

        with transform("mask", Customer.ssn):
            customers = list(Customer.objects.all())
            self.assertEqual(customers[0].ssn, '***-**-1234')

    @staticmethod
    def add_customer():
        customer = Customer()
        customer.name = 'John'
        customer.email = 'JohnA@gmail.com'
        customer.phone = '+972-54-1234567'
        customer.address = 'Tel Aviv'
        customer.dob = '1990-01-01'
        customer.ssn = '123-12-1234'
        customer.save()

        return customer