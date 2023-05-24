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

from django_encryption.vault_wrapper import (EncryptionType, Reason, Vault,
                                             VaultException)

_DECRYPTED_PREFIX = 'decrypted_'
_ENCRYPTED_PREFIX = 'encrypted_'


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

# This function is necessary so that we are able to pass information from the queryset
# to get_prefetch_queryset


def make_iterable_wrapper(transform_fields=None):
    class ModelIterableWrapper(django.db.models.query.ModelIterable):

        def __iter__(self):
            for obj in super().__iter__():
                if self.transform_fields:
                    obj._transform_fields = self.transform_fields
                yield obj
    ModelIterableWrapper.transform_fields = transform_fields
    return ModelIterableWrapper


class EncryptionBatchQuerySet(django.db.models.query.QuerySet):
    """A QuerySet subclass that allows us to support transformations as part of the query, e.g. queryset.mask('field1', 'field2')"""

    MASK_TRANSFORMATION_NAME = 'mask'

    def __init__(self, model=None, query=None, using=None, hints=None):
        super().__init__(model, query, using, hints)
        self._transform_fields = {}

    def transform(self, transformation_name, *fields):
        clone = self._clone()
        for field in fields:
            if isinstance(field, str):
                field_name = field
            elif isinstance(field, EncryptedMixinDescriptor):
                field_name = field.field.name
            else:  # EncryptedMixin
                field_name = field.name
            clone._transform_fields[field_name] = transformation_name
        clone._iterable_class = make_iterable_wrapper(clone._transform_fields)
        return clone

    def mask(self, *fields):
        return self.transform(EncryptionBatchQuerySet.MASK_TRANSFORMATION_NAME, *fields)


class EncryptedBatchManager(django.db.models.Manager):
    def mask(self, *fields):
        return self.get_queryset().mask(*fields)

    def transform(self, transformation_name, *fields):
        return self.get_queryset().transform(transformation_name, *fields)

    def get_queryset(self):
        qs = EncryptionBatchQuerySet(self.model, using=self._db)
        for field in self.model._meta.get_fields():
            if isinstance(field, EncryptedMixin) and field.eager:
                qs = qs.prefetch_related(field.name)
        return qs


class EncryptingModel(django.db.models.Model):
    """Base class for models that use encrypted fields,
    allows for bulk decryption and transformations as part of the queryset"""

    objects = EncryptedBatchManager()

    class Meta:
        abstract = True


# EncryptedMixinDescriptor is a descriptor wrapping access to fields inheriting from EncryptedMixin
# it allows us to:
#   lazily decrypt the field value when it is accessed, and then caching the result
#   bulk decrypt values
class EncryptedMixinDescriptor(DeferredAttribute):

    def __init__(self, field):
        super().__init__(field)

    def __get__(self, instance, owner):
        if instance is None:
            return DeferredAttribute.__get__(self, instance, owner)
        if hasattr(instance, _DECRYPTED_PREFIX + self.field.name):
            decrypted_value = getattr(
                instance, _DECRYPTED_PREFIX + self.field.name)
            return decrypted_value
        if hasattr(instance, _ENCRYPTED_PREFIX + self.field.name):
            encrypted_value = getattr(
                instance, _ENCRYPTED_PREFIX + self.field.name)
            if encrypted_value is None:
                setattr(instance, _DECRYPTED_PREFIX + self.field.name, None)
                return None

            transformation = None
            if hasattr(instance, '_transform_fields'):
                transformation = instance._transform_fields.get(
                    self.field.name)
            decrypted_value = self.field.get_decrypted_value(
                encrypted_value, transformation=transformation)
            setattr(
                instance,
                _DECRYPTED_PREFIX + self.field.name,
                decrypted_value)
            return decrypted_value
        return DeferredAttribute.__get__(self, instance, owner)

    def __set__(self, instance, value):
        if instance is None:
            raise AttributeError("Can only be set on instances")
        if value is None:
            setattr(instance, _DECRYPTED_PREFIX + self.field.name, None)
            setattr(instance, _ENCRYPTED_PREFIX + self.field.name, None)
            return
        if isinstance(value, tuple):
            # we got an encrypted value
            value = value[1]
            setattr(instance, _ENCRYPTED_PREFIX + self.field.name, value)
            return
        # we got a decrypted value
        setattr(instance, _DECRYPTED_PREFIX + self.field.name, value)

    # get_prefetch_queryset is called by django when prefetching related objects
    # this function allows django's queries to believe that the encrypted fields
    # are like foreign keys and so can be prefetched
    def get_prefetch_queryset(self, instances, queryset=None):
        encrypted_attr_name = _ENCRYPTED_PREFIX + self.field.name
        encrypted_values = [getattr(instance, encrypted_attr_name)
                            for instance in instances]
        transformation = None
        # we could actually have a separate transformation for each instance, but we are assuming
        # that it's the same transformation for all of them
        if hasattr(instances[0], '_transform_fields') and self.field.name in instances[0]._transform_fields:
            transformation = instances[0]._transform_fields.get(
                self.field.name)
        rel_qs = self.field.get_decrypted_values(
            encrypted_values, transformation=transformation)

        def rel_obj_attr(obj):
            return _DECRYPTED_PREFIX + self.field.name

        def instance_attr(obj):
            return _DECRYPTED_PREFIX + self.field.name

        single = True
        cache_name = _DECRYPTED_PREFIX + self.field.name
        is_descriptor = True
        return (
            rel_qs,
            rel_obj_attr,
            instance_attr,
            single,
            cache_name,
            is_descriptor)

    def is_cached(self, obj):
        result = hasattr(obj, _DECRYPTED_PREFIX + self.field.name) and getattr(obj,
                                                                               _DECRYPTED_PREFIX + self.field.name) is not None
        return result


class EncryptedMixin(object):
    descriptor_class = EncryptedMixinDescriptor

    def __init__(
            self,
            *args,
            vault_property: Optional[str] = None,
            vault_collection: Optional[str] = None,
            encryption_type: Optional[EncryptionType] = None,
            expiration_secs: Optional[int] = None,
            data_type_name: Optional[str] = None,
            on_error: Any = None,
            eager: bool = True,
            **kwargs):
        self._vault_property = vault_property
        self._vault_collection = vault_collection
        self.encryption_type = encryption_type
        self.expiration_secs = expiration_secs
        self._data_type_name = data_type_name
        self.on_error = on_error
        self.eager = eager

        if 'max_length' in kwargs:
            raise ImproperlyConfigured(
                'max_length is not supported on EncryptedMixin')

        super(EncryptedMixin, self).__init__(*args, **kwargs)

    @property
    def data_type_name(self) -> str:
        if self._data_type_name is None:
            return 'STRING'
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

    # This is a hook for the field, so that when a value is ready from the DB, we know it was read from the DB.
    # This allows us to differentiate between model.field = x done by the developer and the same when done internally by
    # django when reading values from the DB. The first is not encrypted, while the second is.
    def from_db_value(self, value, *args, **kwargs):
        if value is None:
            return None
        if not value:
            return self.to_python(value)
        return ('encrypted', value)

    def get_decrypted_value(self, encrypted_value, transformation=None):
        if encrypted_value is None:
            return None
        if not encrypted_value:
            return self.to_python(encrypted_value)
        vault_collection = self.vault_collection
        field_name = self.vault_property
        if transformation:
            field_name = f'{field_name}.{transformation}'
        try:
            decrypted_value = _VAULT.decrypt(
                ciphertext=encrypted_value,
                field_name=field_name,
                collection=vault_collection,
                reason=None,
            )
        except VaultException:
            if self.on_error == raise_error:
                raise
            else:
                return self.to_python(self.on_error)
        return self.to_python(decrypted_value)

    def get_decrypted_values(self, encrypted_values, transformation=None):
        result = [None] * len(encrypted_values)
        values_to_send = []
        sent_values_idx_to_orig_idx = {}
        vault_collection = self.vault_collection
        field_name = self.vault_property
        if transformation:
            field_name = f'{field_name}.{transformation}'
        for idx, encrypted_value in enumerate(encrypted_values):
            if encrypted_value is None:
                continue
            if not encrypted_value:
                result[idx] = self.to_python(encrypted_value)
                continue
            values_to_send.append(encrypted_value)
            sent_values_idx_to_orig_idx[len(values_to_send) - 1] = idx
        try:
            decrypted_values = _VAULT.bulk_decrypt(
                ciphertexts=values_to_send,
                field_name=field_name,
                reason=None,
                collection=vault_collection,
            )
        except VaultException:
            if self.on_error == raise_error:
                raise
            else:
                decrypted_values = [self.on_error] * len(values_to_send)
        for sent_idx, decrypted_value in enumerate(decrypted_values):
            orig_idx = sent_values_idx_to_orig_idx[sent_idx]
            result[orig_idx] = self.to_python(decrypted_value)
        return result

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


class EncryptedPositiveIntegerField(  # type: ignore
        EncryptedNumberMixin, django.db.models.PositiveIntegerField):
    pass


class EncryptedSmallIntegerField(  # type: ignore
        EncryptedNumberMixin, django.db.models.SmallIntegerField):
    pass


class EncryptedPositiveSmallIntegerField(  # type: ignore
        EncryptedNumberMixin, django.db.models.PositiveSmallIntegerField
):
    pass


class EncryptedBigIntegerField(  # type: ignore
        EncryptedNumberMixin, django.db.models.BigIntegerField):
    pass


class EncryptedSSNField(EncryptedMixin, django.db.models.TextField):
    pass


@contextmanager
def with_reason(reason: Reason):
    _VAULT.add_reason(reason)
    try:
        yield
    finally:
        _VAULT.remove_reason(reason)
