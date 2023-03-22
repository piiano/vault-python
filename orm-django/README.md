# Django Encrypted Model Fields

[![image](https://travis-ci.org/lanshark/django-encrypted-model-fields.png)](https://travis-ci.org/lanshark/django-encrypted-model-fields)

## About

This library allows you to specify specific fields to encrypt in your Django models using Vault's API in a transparent manner, taking advantage of Vault's advanced capabilities.
This helps you:
* Achieve compliance with various privacy standards
* Implement TTL or expiration for data
* Get Masked or transformed versions of your data
* Rely on Vault's permission model


This is a fork of
<https://gitlab.com/lansharkconsulting/django/django-encrypted-model-fields> which in turn is a fork of <https://github.com/foundertherapy/django-cryptographic-fields>. It has
been renamed, and updated to support encryption through Piiano Vault's API.

## Usage

* `pip install piiano-django-encryption`
* Add to your `settings.py`:
  * `VAULT_ADDRESS`
  * `VAULT_API_KEY`
  * `VAULT_DEFAULT_COLLECTION`
  * Note: it is best practice to provide `VAULT_ADDRESS` and `VAULT_API_KEY` via environment variables in production
  * Add `piiano_django_encryption` to `INSTALLED_APPS`
* In your `models.py`:
  * `from piiano_django_encryption.fields import EncryptedCharField` (or any other field type)
  * For each model field you would like to encrypt, replace the field name with `EncryptedCharField` (or any other field type):
    * You can provide additional customization per field:
    * optional `encryption_type` - Can be `EncryptionType.randomized` or `EncryptionType.deterministic`
    * optional `expiration_secs` - An integer or None. If an integer, the number of seconds before the encrypted data is expired, and cannot be decrypted anymore. Works only with randomized `encryption_type`
    * optional `vault_collection` - The name of the vault collection that this field is related to. Defaults to `settings.VAULT_DEFAULT_COLLECTION`
    * optional `vault_property` - The name of the property in the vault collection that this field is related to. Defaults to the name of the field in django.
    * optional `data_type_name` - The name of the data type in vault. Defaults to 'string'. This only has impact when generating a vault migration, and does not change the way your django model would behave.
    * Note: use `vault_collection` together with `vault_property` to specify the collection and property in vault that represent this field. This is important for permission control and audit logs. For more advanced use-cases, this would allow you to transition smoothly to using Vault as a secure storage location for PII data.
  * Query your model as usual:
    * Caveat: right now, an API call to vault will be generated for each field in each Model instance you encrypt or decrypt. In the future this will be batched.
  * You can wrap your queries with: `with fields.mask_field(MyModel.my_field):` (or `transform` or `with_reason`):
    * This tells the encryption SDK to mask the values of MyModel.my_field. So for example, for an SSN you would get "***-**-6789". 
    * All vault's supported transformations are also supported using the `transform` context manager. See [Built-in transformations](https://piiano.com/docs/guides/manage-transformations/built-in-transformations) in Vault's API documentation for a list of Vault's supported transformations.

## Sample code

```
from django.db import models

from piiano_django_encryption.fields import EncryptedCharField, EncryptedEmailField, EncryptedDateField, EncryptionType


class Customer(models.Model):
    name = EncryptedCharField()
    email = EncryptedEmailField()
    phone = EncryptedCharField()
    address = EncryptedCharField(
        encryption_type=EncryptionType.randomized, expiration_secs=10)
    ssn = EncryptedCharField(
        encryption_type=EncryptionType.randomized)
    dob = EncryptedDateField()
```

You can see a full working example in [Piiano's Vault code samples Python repository](https://github.com/piiano/vault-code-samples-python-django).

## Installation for local development

* Clone the repo
* Make sure you have [python poetry](https://python-poetry.org/) installed on your machine (a global installation)
* cd into the directory of the repo
* `poetry install`
* `poetry shell`
* On a mac with vscode: `code .`
* Make sure you have a local copy of vault running
* To run tests: `python manage.py test`
  * Tests should also be available from within vscode.

 