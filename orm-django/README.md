# Django Encrypted Model Fields

[![image](https://travis-ci.org/lanshark/django-encrypted-model-fields.png)](https://travis-ci.org/lanshark/django-encrypted-model-fields)

## About

This is a fork of
<https://gitlab.com/lansharkconsulting/django/django-encrypted-model-fields> which in turn is a fork of <https://github.com/foundertherapy/django-cryptographic-fields>. It has
been renamed, and updated to support encryption through Piiano Vault's API.

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

 