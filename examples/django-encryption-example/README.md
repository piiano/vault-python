<p>
  <a href="https://piiano.com/pii-data-privacy-vault/">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://piiano.com/docs/img/logo-developers-dark.svg">
      <source media="(prefers-color-scheme: light)" srcset="https://piiano.com/wp-content/uploads/piiano-logo-developers.png">
      <img alt="Piiano Vault" src="https://piiano.com/wp-content/uploads/piiano-logo-developers.png" height="40" />
    </picture>
  </a>
</p>

# Django-encryption-example

## About
The sample has been built using the Django web framework and utilizes the [orm-django](https://github.com/piiano/vault-sdk-python/blob/af26c121a9912f97c9ba72f296071600c255023e/sdk/orm-django) to interact with the underlying database. The sample website has several features, including the ability to create and manage users.

As this sample utilizing Piiano vault's features, we are enabled to encrypt / decrypt personal information such as SSN.

## Installation for local development

1. Clone the repo
2. Make sure you have [python poetry](https://python-poetry.org/) installed on your machine (a global installation).
3. cd into the directory of the repo [here](.)

Run the following:
```commandline
poetry shell
```
  **Note** you might have to make sure the django-encryption dependency is already cloned and available in a nearby directory, see pyproject.toml
  * On a Mac with vscode: `code .`

4. Create a local_settings.py, you can just copy local_settings_example.py to local_settings.py locally

**Make sure you have a local copy of vault running** then run the following commands:

`python manage.py migrate`

`python manage.py generate_vault_migration.py > vault_migration.py`

`python vault_migration.py`

`python manage.py runserver`

## Website
After running the project, the website looks like this:

<img src="imgs/website_img.png" alt="website image" width="400" height="350">

We can add a customer by filling the fields for each property (and press "Add customer") like:

<img src="imgs/add_customer_img.png" alt="add customer image" width="250" height="300">

Then a new customer will appear with the given values:

<img src="imgs/customer_details_img.png" alt="website image" width="500" height="100">
