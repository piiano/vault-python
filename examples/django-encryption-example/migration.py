

import os
from typing import Dict, List

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vault_sample_django.settings")

from django_encryption.fields import VaultException, get_vault  # noqa


COLLECTION_TO_FIELDS: Dict[str, List[str]] = {
    'persons': ['name', 'email', 'phone', 'address', 'ssn', 'dob']}


def main():
    vault = get_vault()
    for collection_name, fields in COLLECTION_TO_FIELDS.items():
        try:
            vault.add_collection(collection_name, 'PERSONS', [])
        except VaultException as e:
            print(e)
        for field in fields:
            try:
                vault.add_property(
                    property_name=field,
                    collection=collection_name,
                    description='',
                    is_encrypted=True,
                    is_index=False,
                    is_nullable=True,
                    is_unique=False,
                    data_type_name='string',
                )
            except VaultException as e:
                print(e)


if __name__ == '__main__':
    main()
