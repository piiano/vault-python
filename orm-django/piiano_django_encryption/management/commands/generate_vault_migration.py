from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Model

from piiano_django_encryption.fields import get_vault


class Command(BaseCommand):
    help = 'Generates a new Vault Migration script'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vault = get_vault()

    def add_arguments(self, parser):
        parser.add_argument('model_names', nargs='+', type=str)

    def _get_all_models(self):
        return apps.get_models()

    def _model_name_to_model(self, model_name: str) -> Model:
        app_label, model_name = model_name.split('.')
        return apps.get_model(app_label, model_name)  # type: ignore

    def _generate_migration(self, model: Model):
        pass

    def handle(self, *args, **options):

        model_names = options['model_names']
        if model_names:
            models = [self._model_name_to_model(name) for name in model_names]
        else:
            models = self._get_all_models()
        for model in models:
            if model.__name__ in model_names:
                self.stdout.write('Generating migration for model: {}'.format(model.__name__))
                self._generate_migration(model)
