
import os
from typing import Dict, List

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vault_sample_django.settings")

from django_encryption.fields import VaultException, get_vault # noqa


COLLECTION_TO_FIELDS: Dict[str, List[str]] = {'persons': [{'name': 'name', 'type': 'string'}, {'name': 'email', 'type': 'string'}, {'name': 'phone', 'type': 'string'}, {'name': 'address', 'type': 'string'}, {'name': 'ssn', 'type': 'string'}, {'name': 'dob', 'type': 'string'}]} 


def main():
    vault = get_vault()
    for collection_name, fields in COLLECTION_TO_FIELDS.items():
        try:
            vault.add_collection(collection_name, 'PERSONS', [])
        except VaultException:
            pass
        for field in fields:
            name = field['name']
            data_type = field['type']
            try:
                vault.add_property(
                    property_name=name,
                    collection=collection_name,
                    description='',
                    is_encrypted=True,
                    is_index=False,
                    is_nullable=True,
                    is_unique=False,
                    data_type_name=data_type,
                )
            except VaultException:
                pass


if __name__ == '__main__':
    main()


