import datetime

from django_encryption.fields import get_vault, EncryptedMixin, VaultException, mask_field, transform
from customers.models import Customer
from django.test import TestCase
from django.urls import reverse


# Create your tests here.
TEST_COLLECTION_NAME = "customers"

TEST_NAME = "John"
TEST_EMAIL = "JohnA@gmail.com"
TEST_PHONE = "+16505551234"
TEST_SSN = "123-12-1234"
MASK_SSN = "***-**-1234"
TEST_DOB = "1990-01-01"
TEST_STATE = "CA"


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

    def test_customer_model(self):
        self.add_customer()

        customers = list(Customer.objects.all())
        assert len(customers) == 1

        # Check that the data is returned as expected
        customer = customers[0]
        self.assertEqual(customer.name, TEST_NAME)
        self.assertEqual(customer.email, TEST_EMAIL)
        self.assertEqual(customer.phone, TEST_PHONE)
        # test the string representation of the Date of Birth
        self.assertEqual(customer.dob.strftime("%Y-%m-%d"), TEST_DOB)
        self.assertEqual(customer.ssn, TEST_SSN)

    def test_encrypted_fields(self):
        self.add_customer()

        with transform("mask", Customer.ssn):
            customers = list(Customer.objects.all())
            self.assertEqual(customers[0].ssn, MASK_SSN)

    @staticmethod
    def add_customer():
        customer = Customer()
        customer.name = TEST_NAME
        customer.email = TEST_EMAIL
        customer.phone = TEST_PHONE
        customer.state = TEST_STATE
        customer.dob = TEST_DOB
        customer.ssn = TEST_SSN
        customer.save()

        return customer

    def test_add_customer_view(self):
        params = {
            "name": TEST_NAME,
            "email": TEST_EMAIL,
            "ssn": TEST_SSN,
            "dob": TEST_DOB,
            "phone": TEST_PHONE,
            "state": TEST_STATE,
        }
        res = self.client.post(reverse('add_customer'), data=params)
        self.assertEqual(res.status_code, 302)

        res = self.client.get(reverse('index'))
        self.assertEqual(res.status_code, 200)

        self.assertContains(res, params['name'])
        self.assertContains(res, params['email'])
        self.assertContains(res, params['state'])
        print(res.content)
        self.assertContains(res, datetime.datetime.strptime(
            params['dob'], "%Y-%m-%d").strftime("%b. %-d, %Y"))
        with mask_field(Customer.ssn):
            self.assertContains(res, '***-**-1234')
