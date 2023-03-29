import itertools
from contextlib import contextmanager
from typing import Any, Optional

import django.db
import django.db.models
from django.conf import settings
from django.core import validators
from django.core.exceptions import ImproperlyConfigured
from django.db.models.options import Options
from django.db.models.query_utils import DeferredAttribute
from django.utils import timezone
from django.utils.functional import cached_property

from django_encryption.vault_wrapper import (EncryptionType, Reason,
                                                    Vault, VaultException)


def get_vault():
    vault_address = getattr(settings, 'VAULT_ADDRESS', None)
    vault_api_key = getattr(settings, 'VAULT_API_KEY', None)
    default_collection = getattr(settings, "VAULT_DEFAULT_COLLECTION", None)

    if not vault_address:
        raise ImproperlyConfigured('VAULT_ADDRESS must be defined in settings')
    if not vault_api_key:
        raise ImproperlyConfigured('VAULT_API_KEY must be defined in settings')

    return Vault(vault_address, vault_api_key, default_collection)


_VAULT = get_vault()


class _RaiseError:
    pass


raise_error = _RaiseError()


class WithVaultOptions(Options):
    vault_collection: Optional[str] = None


class EncryptedMixin(object):
    def __init__(
            self,
            *args,
            vault_property: Optional[str] = None,
            vault_collection: Optional[str] = None,
            encryption_type: Optional[EncryptionType] = None,
            expiration_secs: Optional[int] = None,
            data_type_name: Optional[str] = None,
            on_error: Any = None,
            **kwargs):
        self._vault_property: Optional[str] = vault_property
        self._vault_collection = vault_collection
        self.encryption_type = encryption_type
        self.expiration_secs = expiration_secs
        self._data_type_name = data_type_name
        self.on_error = on_error

        if 'max_length' in kwargs:
            raise ImproperlyConfigured(
                'max_length is not supported on EncryptedMixin')

        super(EncryptedMixin, self).__init__(*args, **kwargs)

    @property
    def data_type_name(self) -> str:
        if self._data_type_name is None:
            return 'string'
        return self._data_type_name

    @property
    def vault_property(self) -> str:
        if self._vault_property is None:
            return self.name  # type: ignore
        return self._vault_property

    @property
    def vault_collection(self):
        vault_collection = self._vault_collection
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
        vault_collection = self.vault_collection
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

        vault_collection = self.vault_collection

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
    @cached_property
    def validators(self):  # type: ignore[override]
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


class EncryptedIntegerField(EncryptedNumberMixin, django.db.models.IntegerField):  # type: ignore
    pass


# type: ignore
class EncryptedPositiveIntegerField(EncryptedNumberMixin, django.db.models.PositiveIntegerField):  # type: ignore
    pass


# type: ignore
class EncryptedSmallIntegerField(EncryptedNumberMixin, django.db.models.SmallIntegerField):  # type: ignore
    pass


class EncryptedPositiveSmallIntegerField(  # type: ignore
        EncryptedNumberMixin, django.db.models.PositiveSmallIntegerField
):
    pass


# type: ignore
class EncryptedBigIntegerField(EncryptedNumberMixin, django.db.models.BigIntegerField):  # type: ignore
    pass


class EncryptedSSNField(EncryptedMixin, django.db.models.TextField):
    pass


@contextmanager
def mask_field(field: EncryptedMixin):
    if isinstance(field, DeferredAttribute):
        field = field.field  # type: ignore
    _VAULT.mask(field.vault_property, field.vault_collection)
    try:
        yield
    finally:
        _VAULT.remove_mask(field.vault_property, field.vault_collection)


@contextmanager
def transform(transformation_name, field: EncryptedMixin):
    if isinstance(field, DeferredAttribute):
        field = field.field  # type: ignore
    _VAULT.add_transformation(field_name=field.vault_property,
                              collection_name=field.vault_collection, transformation_name=transformation_name)
    try:
        yield
    finally:
        _VAULT.remove_transformation(
            field_name=field.vault_property, collection_name=field.vault_collection)


@contextmanager
def with_reason(reason: Reason):
    _VAULT.add_reason(reason)
    try:
        yield
    finally:
        _VAULT.remove_reason(reason)
