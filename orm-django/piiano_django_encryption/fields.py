import enum
import inspect
import itertools
from contextlib import contextmanager
from typing import Optional, Union

import django.db
import django.db.models
from django.conf import settings
from django.core import validators
from django.core.exceptions import ImproperlyConfigured
from django.db.models.options import Options
from django.db.models.query_utils import DeferredAttribute
from django.utils import timezone
from django.utils.functional import cached_property

from piiano_django_encryption.vault_wrapper import (EncryptionType, Reason,
                                                    Vault, VaultException)


def get_vault():
    print("in get_vault, stack: ", list(
        itertools.islice(reversed(inspect.stack()), 0, 10)))
    print(settings)
    vault_address = getattr(settings, 'VAULT_ADDRESS', None)
    vault_api_key = getattr(settings, 'VAULT_API_KEY', None)
    default_collection = getattr(settings, "VAULT_DEFAULT_COLLECTION", None)
    print(vault_address, vault_api_key, default_collection)

    if not vault_address:
        raise ImproperlyConfigured('VAULT_ADDRESS must be defined in settings')
    if not vault_api_key:
        raise ImproperlyConfigured('VAULT_API_KEY must be defined in settings')

    return Vault(vault_address, vault_api_key, default_collection)


_VAULT = get_vault()


class RaiseError:
    pass


raise_error = RaiseError()


class WithVaultOptions(Options):
    vault_collection: Optional[str] = None


class EncryptedMixin(object):
    def __init__(self, *args, **kwargs):
        self._vault_property: Optional[str] = kwargs.pop(
            'vault_property', None)

        if 'vault_collection' in kwargs:
            self.vault_collection = kwargs.pop('vault_collection')
        else:
            self.vault_collection = None
        if 'encryption_type' in kwargs:
            self.encryption_type = kwargs.pop('encryption_type')
        else:
            self.encryption_type = None
        if 'expiration_secs' in kwargs:
            self.expiration_secs = kwargs.pop('expiration_secs')
        else:
            self.expiration_secs = None
        if 'on_error' in kwargs:
            self.on_error = kwargs.pop('on_error')
        else:
            self.on_error = None
        if 'max_length' in kwargs:
            raise ImproperlyConfigured(
                'max_length is not supported on EncryptedMixin')

        super(EncryptedMixin, self).__init__(*args, **kwargs)

    @ property
    def vault_property(self) -> str:
        if self._vault_property is None:
            return self.name  # type: ignore
        return self._vault_property

    def _get_vault_collection(self):
        vault_collection = self.vault_collection
        if vault_collection is None:
            meta = self.model._meta
            vault_collection = getattr(meta, 'vault_collection', None)
        if vault_collection is None:
            vault_collection = _VAULT.default_collection
        return vault_collection

    def from_db_value(self, value, *args, **kwargs):
        if value is None:
            return None
        if not value:
            return self.to_python(value)
        vault_collection = self._get_vault_collection()
        try:
            value = _VAULT.decrypt(
                ciphertext=value,
                field_name=self.vault_property,
                collection=vault_collection,
                reason=None,
            )
        except VaultException:
            if self.on_error == raise_error:
                raise
            else:
                return self.to_python(self.on_error)
        return self.to_python(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        value = super(EncryptedMixin, self).get_db_prep_value(
            value, connection, prepared)

        if value is None:
            return value

        vault_collection = self._get_vault_collection()

        # decode the encrypted value to a unicode string, else this breaks in pgsql
        result = _VAULT.encrypt(
            plaintext=str(value),
            field_name=self.vault_property,
            collection=vault_collection,
            reason=None,
            encryption_type=self.encryption_type,
            expiration_secs=self.expiration_secs)
        return result

    def get_internal_type(self):
        return "TextField"

    def deconstruct(self):
        name, path, args, kwargs = super(EncryptedMixin, self).deconstruct()

        if 'max_length' in kwargs:
            del kwargs['max_length']

        return name, path, args, kwargs


class EncryptedCharField(EncryptedMixin, django.db.models.TextField):
    pass


class EncryptedTextField(EncryptedMixin, django.db.models.TextField):
    pass


class EncryptedDateField(EncryptedMixin, django.db.models.DateField):
    pass


class EncryptedDateTimeField(EncryptedMixin, django.db.models.DateTimeField):
    # credit to Oleg Pesok...
    def to_python(self, value):
        value = super(EncryptedDateTimeField, self).to_python(value)

        if value is not None and settings.USE_TZ and timezone.is_naive(value):
            default_timezone = timezone.get_default_timezone()
            value = timezone.make_aware(value, default_timezone)

        return value


class EncryptedEmailField(EncryptedMixin, django.db.models.EmailField):
    pass


class EncryptedBooleanField(EncryptedMixin, django.db.models.BooleanField):

    def get_db_prep_save(self, value, connection):
        if value is None:
            return value
        if value is True:
            value = '1'
        elif value is False:
            value = '0'
        return super(EncryptedBooleanField, self).get_db_prep_save(value, connection)
        # decode the encrypted value to a unicode string, else this breaks in pgsql
        # return encrypt_str(str(value)).decode('utf-8')


class EncryptedNumberMixin(EncryptedMixin):
    max_length = 20

    @ cached_property
    def validators(self):
        # These validators can't be added at field initialization time since
        # they're based on values retrieved from `connection`.
        range_validators = []
        internal_type = self.__class__.__name__[9:]
        min_value, max_value = django.db.connection.ops.integer_field_range(
            internal_type)
        if min_value is not None:
            range_validators.append(validators.MinValueValidator(min_value))
        if max_value is not None:
            range_validators.append(validators.MaxValueValidator(max_value))
        return list(itertools.chain(self.default_validators, self._validators, range_validators))


class EncryptedIntegerField(EncryptedNumberMixin, django.db.models.IntegerField):
    description = "An IntegerField that is encrypted before " \
        "inserting into a database using the python cryptography " \
        "library"
    pass


class EncryptedPositiveIntegerField(EncryptedNumberMixin, django.db.models.PositiveIntegerField):
    pass


class EncryptedSmallIntegerField(EncryptedNumberMixin, django.db.models.SmallIntegerField):
    pass


class EncryptedPositiveSmallIntegerField(
        EncryptedNumberMixin, django.db.models.PositiveSmallIntegerField
):
    pass


class EncryptedBigIntegerField(EncryptedNumberMixin, django.db.models.BigIntegerField):
    pass


@ contextmanager
def mask_field(field: EncryptedMixin):
    if isinstance(field, DeferredAttribute):
        field = field.field  # type: ignore
    _VAULT.mask(field.vault_property, field.vault_collection)
    try:
        yield
    finally:
        _VAULT.remove_mask(field.vault_property, field.vault_collection)


@ contextmanager
def with_reason(reason: Reason):
    _VAULT.add_reason(reason)
    try:
        yield
    finally:
        _VAULT.remove_reason(reason)
