<p>
  <a href="https://piiano.com/pii-data-privacy-vault/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://piiano.com/docs/img/logo-developers-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="https://piiano.com/wp-content/uploads/piiano-logo-developers.png">
      <img alt="Piiano Vault" src="https://piiano.com/wp-content/uploads/piiano-logo-developers.png" height="40" />
    </picture>
  </a>
</p>

# Django Encrypted Model Fields
[![Coverage Status](./imgs/coverage.svg)](https://github.com/piiano/vault-python/sdk/orm-django/imgs/coverage.svg)
![Workflow status badge](https://github.com/piiano/vault-python/actions/workflows/test-orm-django.yml/badge.svg?branch=main)
![Python version badge](https://img.shields.io/pypi/pyversions/spleeter)

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

First install the library:
```commandline
pip install django-encryption
```

Add to your `settings.py` (Example in [here](../../examples/django-encryption-example/vault_sample_django/local_settings_example.py)):
  * `VAULT_ADDRESS`
  * `VAULT_API_KEY`
  * `VAULT_DEFAULT_COLLECTION`
  **Note** it is best practice to provide `VAULT_ADDRESS` and `VAULT_API_KEY` via environment variables in production 
  * Add `django_encryption` to `INSTALLED_APPS`

In your `models.py` (Example in [here](../../examples/django-encryption-example/customers/models.py)):

1. Import any desired field type, for example:
```python
from django_encryption.fields import EncryptedCharField
```

2. For each model field you would like to encrypt, replace the field name with any of the fields you imported in step 1 (For example, `EncryptedCharField`).

    You can customize the field by providing additional parameters such as:
    * `encryption_type` (**optional**) - Can be `EncryptionType.randomized` or `EncryptionType.deterministic`
    * `expiration_secs` (**optional**) - An integer or None. If an integer, the number of seconds before the encrypted data is expired, and cannot be decrypted anymore. Works only with randomized `encryption_type`
    * `vault_collection` (**optional**) - The name of the vault collection that this field is related to. Defaults to `settings.VAULT_DEFAULT_COLLECTION`
    * `vault_property` (**optional**) - The name of the property in the vault collection that this field is related to. Defaults to the name of the field in django.
    * `data_type_name` (**optional**) - The name of the data type in vault. Defaults to 'string'. This only has impact when generating a vault migration, and does not change the way your django model would behave.
   
   **Note**: use `vault_collection` together with `vault_property` to specify the collection and property in vault that represent this field. This is important for permission control and audit logs. For more advanced use-cases, this would allow you to transition smoothly to using Vault as a secure storage for PII data.
 

Query your model as usual:
  * Caveat: right now, an API call to vault will be generated for each field in each Model instance you encrypt or decrypt. In the future this will be batched.
   
   
You can wrap your queries with: `with fields.mask_field(MyModel.my_field):` (or `transform` or `with_reason`):
  * This tells the encryption SDK to mask the values of MyModel.my_field. So for example, for an SSN you would get "***-**-6789". 
  * All vault's supported transformations are also supported using the `transform` context manager. See [Built-in transformations](https://piiano.com/docs/guides/manage-transformations/built-in-transformations) in Vault's API documentation for a list of Vault's supported transformations.

## Sample code

```
from django.db import models
from django_encryption.fields import EncryptedCharField, EncryptedEmailField, EncryptedDateField, EncryptionType


class Customer(models.Model):
    name = EncryptedCharField()
    email = EncryptedEmailField()
    phone = EncryptedCharField()
    address = EncryptedCharField(encryption_type=EncryptionType.randomized, expiration_secs=10)
    ssn = EncryptedCharField(encryption_type=EncryptionType.randomized)
    dob = EncryptedDateField()
```

You can see a full working example in [our sample](https://github.com/piiano/vault-python/tree/main/examples/django-encryption-example).

## Installation for local development

* Clone the repo
* Make sure you have [python poetry](https://python-poetry.org/) installed on your machine (a global installation)
* cd into the directory of the repo (sdk/orm-django)

Run the following commands:
```commandline
poetry install
poetry shell
```
  * On a Mac with vscode: `code .`

To run tests: `python manage.py test`
  * Tests should also be available from within vscode.

**NOTE** Make sure you have a local copy of vault running on your machine. To do so, follow the [Installations Instructions](https://piiano.com/docs/guides/get-started/).
