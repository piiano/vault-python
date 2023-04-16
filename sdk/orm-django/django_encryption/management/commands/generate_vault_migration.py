from collections import defaultdict
from typing import DefaultDict, List, Optional

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Model

from django_encryption.fields import EncryptedMixin, get_vault


class Command(BaseCommand):
    help = 'Generates a new Vault Migration script'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vault = get_vault()

    def add_arguments(self, parser):
        parser.add_argument('model_names', nargs='*', type=str)

    def _get_all_models(self):
        return apps.get_models()

    def _model_name_to_model(self, model_name: str) -> Model:
        app_label, model_name = model_name.split('.')
        return apps.get_model(app_label, model_name)  # type: ignore

    def _get_django_project_name(self):
        return settings.ROOT_URLCONF.split('.')[0]

    def _generate_migration(self, model_names: Optional[List[str]] = None) -> str:
        collection_to_fields: DefaultDict[str, list] = defaultdict(list)

        if model_names:
            models = [self._model_name_to_model(name) for name in model_names]
        else:
            models = self._get_all_models()
        for model in models:
            for field in model._meta.get_fields():
                if not isinstance(field, EncryptedMixin):
                    continue
                collection = field.vault_collection
                property_name = field.vault_property
                property_type = field.data_type_name
                collection_to_fields[collection].append(dict(name=property_name, type=property_type))
        template = TEMPLATE
        project_name = self._get_django_project_name()
        template = template.replace('__PROJECT_NAME__', project_name)
        template = template.replace('__COLLECTION_TO_FIELDS__', repr(dict(collection_to_fields)))
        return template

    def handle(self, *args, **options):
        model_names = options.get('model_names')
        migration_script = self._generate_migration(model_names)
        print(migration_script)


TEMPLATE = """
import os
from typing import Dict, List

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "__PROJECT_NAME__.settings")
import django
django.setup()

from django_encryption.fields import VaultException, get_vault # noqa


COLLECTION_TO_FIELDS: Dict[str, List[str]] = __COLLECTION_TO_FIELDS__ 


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

"""
