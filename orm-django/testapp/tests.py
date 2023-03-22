import datetime
import os
import mock
import sys
import time
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.forms import ModelForm
from django.test import TestCase
from django.utils import timezone

import piiano_django_encryption.fields
from piiano_django_encryption import fields
from piiano_django_encryption.fields import (EncryptedMixin, VaultException,
                                             get_vault, mask_field, transform)

from . import models

TEST_COLLECTION_NAME = 'test'


class TestSettings(TestCase):

    def test_settings(self):
        with self.settings(VAULT_ADDRESS='http://localhost:8123', VAULT_API_KEY='test'):
            fields.get_vault()

    def test_settings_empty(self):
        with self.settings(VAULT_ADDRESS='', VAULT_API_KEY='test', VAULT_DEFAULT_COLLECTION='test'):
            self.assertRaises(ImproperlyConfigured, fields.get_vault)

        with self.settings(VAULT_ADDRESS='http://localhost:8123', VAULT_API_KEY='', VAULT_DEFAULT_COLLECTION='test'):
            self.assertRaises(ImproperlyConfigured, fields.get_vault)


class TestModelTestCase(TestCase):

    def setUp(self) -> None:

        vault = get_vault()
        vault.add_collection(TEST_COLLECTION_NAME, 'PERSONS', [])
        try:
            for field in models.TestModel._meta.get_fields():
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

    def test_value(self):
        test_date_today = datetime.date.today()
        test_date = datetime.date(2011, 1, 1)
        test_datetime = datetime.datetime(2011, 1, 1, 1, tzinfo=timezone.utc)
        inst = models.TestModel()
        inst.enc_char_field = 'This is a test string!'
        inst.enc_text_field = 'This is a test string2!'
        inst.enc_date_field = test_date
        inst.enc_datetime_field = test_datetime
        inst.enc_boolean_field = True
        inst.enc_integer_field = 123456789
        inst.enc_positive_integer_field = 123456789
        inst.enc_small_integer_field = 123456789
        inst.enc_positive_small_integer_field = 123456789
        inst.enc_big_integer_field = 9223372036854775807
        inst.enc_ssn_field = '123-45-6789'
        inst.save()

        inst = models.TestModel.objects.get()
        self.assertEqual(inst.enc_char_field, 'This is a test string!')
        self.assertEqual(inst.enc_text_field, 'This is a test string2!')
        self.assertEqual(inst.enc_date_field, test_date)
        self.assertEqual(inst.enc_date_now_field, test_date_today)
        self.assertEqual(inst.enc_date_now_add_field, test_date_today)
        self.assertEqual(inst.enc_datetime_field, test_datetime)
        self.assertEqual(inst.enc_boolean_field, True)
        self.assertEqual(inst.enc_integer_field, 123456789)
        self.assertEqual(inst.enc_positive_integer_field, 123456789)
        self.assertEqual(inst.enc_small_integer_field, 123456789)
        self.assertEqual(inst.enc_positive_small_integer_field, 123456789)
        self.assertEqual(inst.enc_big_integer_field, 9223372036854775807)
        self.assertEqual(inst.enc_ssn_field, '123-45-6789')

        test_date = datetime.date(2012, 2, 1)
        test_datetime = datetime.datetime(2012, 1, 1, 2, tzinfo=timezone.utc)
        inst.enc_char_field = 'This is another test string!'
        inst.enc_text_field = 'This is another test string2!'
        inst.enc_date_field = test_date
        inst.enc_datetime_field = test_datetime
        inst.enc_boolean_field = False
        inst.enc_integer_field = -123456789
        inst.enc_positive_integer_field = 0
        inst.enc_small_integer_field = -123456789
        inst.enc_positive_small_integer_field = 0
        inst.enc_big_integer_field = -9223372036854775806
        inst.enc_ssn_field = '987-65-4321'
        inst.save()

        inst = models.TestModel.objects.get()
        self.assertEqual(inst.enc_char_field, 'This is another test string!')
        self.assertEqual(inst.enc_text_field, 'This is another test string2!')
        self.assertEqual(inst.enc_date_field, test_date)
        self.assertEqual(inst.enc_date_now_field, datetime.date.today())
        self.assertEqual(inst.enc_date_now_add_field, datetime.date.today())
        # be careful about sqlite testing, which doesn't support native dates
        if timezone.is_naive(inst.enc_datetime_field):
            inst.enc_datetime_field = timezone.make_aware(inst.enc_datetime_field, timezone.utc)
        self.assertEqual(inst.enc_datetime_field, test_datetime)
        self.assertEqual(inst.enc_boolean_field, False)
        self.assertEqual(inst.enc_integer_field, -123456789)
        self.assertEqual(inst.enc_positive_integer_field, 0)
        self.assertEqual(inst.enc_small_integer_field, -123456789)
        self.assertEqual(inst.enc_positive_small_integer_field, 0)
        self.assertEqual(inst.enc_big_integer_field, -9223372036854775806)
        self.assertEqual(inst.enc_ssn_field, '987-65-4321')

        inst.save()
        inst = models.TestModel.objects.get()

    def test_unicode_value(self):
        inst = models.TestModel()
        inst.enc_char_field = u'\xa2\u221e\xa7\xb6\u2022\xaa'
        inst.enc_text_field = u'\xa2\u221e\xa7\xb6\u2022\xa2'
        inst.save()

        inst2 = models.TestModel.objects.get()
        self.assertEqual(inst2.enc_char_field, u'\xa2\u221e\xa7\xb6\u2022\xaa')
        self.assertEqual(inst2.enc_text_field, u'\xa2\u221e\xa7\xb6\u2022\xa2')

    def test_get_internal_type(self):
        enc_char_field = models.TestModel._meta.fields[1]
        enc_text_field = models.TestModel._meta.fields[2]
        enc_date_field = models.TestModel._meta.fields[3]
        enc_date_now_field = models.TestModel._meta.fields[4]
        enc_boolean_field = models.TestModel._meta.fields[7]
        enc_integer_field = models.TestModel._meta.fields[8]
        enc_positive_integer_field = models.TestModel._meta.fields[9]
        enc_small_integer_field = models.TestModel._meta.fields[10]
        enc_positive_small_integer_field = models.TestModel._meta.fields[11]
        enc_big_integer_field = models.TestModel._meta.fields[12]
        enc_ss_field = models.TestModel._meta.fields[13]

        self.assertEqual(enc_char_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_text_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_date_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_date_now_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_boolean_field.get_internal_type(), 'TextField')

        self.assertEqual(enc_integer_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_positive_integer_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_small_integer_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_positive_small_integer_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_big_integer_field.get_internal_type(), 'TextField')
        self.assertEqual(enc_ss_field.get_internal_type(), 'TextField')

    def test_auto_date(self):
        enc_date_now_field = models.TestModel._meta.fields[4]
        self.assertEqual(enc_date_now_field.name, 'enc_date_now_field')
        self.assertTrue(enc_date_now_field.auto_now)

        enc_date_now_add_field = models.TestModel._meta.fields[5]
        self.assertEqual(enc_date_now_add_field.name, 'enc_date_now_add_field')
        self.assertFalse(enc_date_now_add_field.auto_now)

        self.assertFalse(enc_date_now_field.auto_now_add)
        self.assertTrue(enc_date_now_add_field.auto_now_add)

    @mock.patch('django.db.connection.ops.integer_field_range')
    def test_integer_field_validators(self, integer_field_range):
        def side_effect(arg):
            # throw error as mysql does in this case
            if arg == 'TextField':
                raise KeyError(arg)
            # benign return value
            return (None, None)

        integer_field_range.side_effect = side_effect

        class TestModelForm(ModelForm):
            class Meta:
                model = models.TestModel
                fields = ('enc_integer_field', )

        f = TestModelForm(data={'enc_integer_field': 99})
        self.assertTrue(f.is_valid())

        inst = models.TestModel()
        # Should be safe to call
        super(
            piiano_django_encryption.fields.EncryptedIntegerField,
            inst._meta.get_field('enc_integer_field')
        ).validators

        # should fail due to error
        with self.assertRaises(Exception):
            super(
                piiano_django_encryption.fields.EncryptedNumberMixin,
                inst._meta.get_field('enc_integer_field')
            ).validators

    def test_mask_value(self):
        inst = models.TestModel()

        inst.enc_ssn_field = '856-45-6789'
        inst.save()
        with transform("mask", inst._meta.fields[13]):
            objects = list(models.TestModel.objects.all())
            self.assertEqual(objects[0].enc_ssn_field, '***-**-6789')

    def test_data_type_name(self):
        enc_char_field = models.TestModel._meta.fields[1]
        enc_ss_field = models.TestModel._meta.fields[13]
        self.assertEqual(enc_char_field.data_type_name, 'string')
        self.assertEqual(enc_ss_field.data_type_name, 'SSN')

    # def test_migration(self):
    #     stdout_backup, sys.stdout = sys.stdout, open('./testapp/vault_migration.py', 'w+')
    #     call_command('generate_vault_migration')
    #     sys.stdout = stdout_backup
    #     os.system("python3 ./testapp/vault_migration.py")
