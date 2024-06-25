<a href="https://piiano.com/pii-data-privacy-vault/">
   <img alt="Piiano Vault" src="https://docs.piiano.com/img/logo-developers.svg" height="40" />
</a>

# Django Encrypted Model Fields

![coverage](https://user-images.githubusercontent.com/90671989/228512586-414c17c9-fbeb-4c47-8971-6541ec00d963.svg)
![Workflow status badge](https://github.com/piiano/vault-python/actions/workflows/test-orm-django.yml/badge.svg?branch=main)
![Python version badge](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C3.10%20%7C%203.11-blue.svg)
[![PyPI version](https://img.shields.io/pypi/v/django-encryption?color=brightgreen)](https://pypi.org/project/django-encryption/)

## About

This library allows you to specify specific fields to encrypt in your Django models using Vault's API in a transparent manner, taking advantage of Vault's advanced capabilities.
This helps you:

- Achieve compliance with various privacy standards
- Implement TTL or expiration for data
- Get Masked or transformed versions of your data
- Rely on Vault's permission model

This is a fork of
<https://gitlab.com/lansharkconsulting/django/django-encrypted-model-fields> which in turn is a fork of <https://github.com/foundertherapy/django-cryptographic-fields>. It has
been renamed, and updated to support encryption through Piiano Vault's API.

**Note:**

Actively tested with Python 3.11.5. Should work with any Python 3.x.
This package is compatible with Vault version 1.11.4.
For a Vault client compatible with other versions of Vault, check [other versions of this package](https://pypi.org/project/django-encryption/).


## Usage

First install the library:

```commandline
pip install django-encryption
```

Add to your `settings.py` (Example in [here](../../examples/django-encryption-example/vault_sample_django/local_settings_example.py)):

- `VAULT_ADDRESS`
- `VAULT_API_KEY`
- `VAULT_DEFAULT_COLLECTION`
  **Note** it is best practice to provide `VAULT_ADDRESS` and `VAULT_API_KEY` via environment variables in production
- Add `django_encryption` to `INSTALLED_APPS`

In your `models.py` (Example in [here](../../examples/django-encryption-example/customers/models.py)):

1. Import any desired field type, for example:

```python
from django_encryption.fields import EncryptedCharField
```

2. For each model field you would like to encrypt, replace the field name with any of the fields you imported in step 1 (For example, `EncryptedCharField`).

   You can customize the field by providing additional parameters such as:

   - `encryption_type` (**optional**) - Can be `EncryptionType.randomized` or `EncryptionType.deterministic`
   - `expiration_secs` (**optional**) - An integer or None. If an integer, the number of seconds before the encrypted data is expired, and cannot be decrypted anymore. Works only with randomized `encryption_type`
   - `vault_collection` (**optional**) - The name of the vault collection that this field is related to. Defaults to `settings.VAULT_DEFAULT_COLLECTION`
   - `vault_property` (**optional**) - The name of the property in the vault collection that this field is related to. Defaults to the name of the field in django.
   - `data_type_name` (**optional**) - The name of the data type in vault. Defaults to 'string'. This only has impact when generating a vault migration, and does not change the way your django model would behave.
   - `eager` (default: **true**) - whether or not value will be decrypted (in a batch operation) as soon as it is fetched from the DB. If not, the value will be decrypted the first time it is accessed.

   **Note**: use `vault_collection` together with `vault_property` to specify the collection and property in vault that represent this field. This is important for permission control and audit logs. For more advanced use-cases, this would allow you to transition smoothly to using Vault as a secure storage for PII data.

Query your model as usual, keeping the following in mind:

* Read queries are batched. Reading from the Database will generate a single API call per field. Writing to the Database is not batched and will generate an API call for each field in each instance.
* By default all fields are eagerly fetched - similarly to calling prefetch_related(field_name) on a foreign key.

The SDK also supports masking and other vault transformations by using mask(MyModel.my_field) or transform('transformation-name', MyModel.my_field) as part of the query.

- This tells the encryption SDK to mask the values of MyModel.my_field. So for example, for an SSN you would get "**\*-**-6789".
- All vault's supported transformations are also supported using the `transform` context manager. See [Built-in transformations](https://piiano.com/docs/guides/manage-transformations/built-in-transformations) in Vault's API documentation for a list of Vault's supported transformations.

## Sample code

```
from django.db import models
from django_encryption.fields import EncryptedCharField, EncryptedEmailField, EncryptedDateField, EncryptionType


class Customer(models.Model):
    name = EncryptedCharField(data_type_name='NAME')
    email = EncryptedEmailField(data_type_name='EMAIL')
    phone = EncryptedCharField(
        data_type_name='PHONE_NUMBER', null=True, blank=True)
    ssn = EncryptedCharField(
        encryption_type=EncryptionType.randomized, data_type_name='SSN', null=True, blank=True)
    dob = EncryptedDateField(
        data_type_name='DATE_OF_BIRTH', null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
```

You can see a full working example in [our sample](https://github.com/piiano/vault-python/tree/main/examples/django-encryption-example).

## Installation for local development (with VSCode)

1. Clone the repo: `git clone https://github.com/piiano/vault-python`
1. Ensure you have [python poetry](https://python-poetry.org/) installed on your machine (a global installation). Example: `pipx install poetry`
1. Run the following commands from the `sdk/orm-django` directory:
   ```commandline
   poetry install
   poetry shell
   code .
   ```
1. To run tests: `python manage.py test`. Tests should also be available from within vscode.

**NOTE** Make sure you have a local copy of vault running on your machine. To do so, follow the [Installations Instructions](https://piiano.com/docs/guides/get-started/).
