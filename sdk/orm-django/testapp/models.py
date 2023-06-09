from django_encryption import fields


class TestModel(fields.EncryptingModel):
    enc_char_field = fields.EncryptedCharField()
    enc_text_field = fields.EncryptedTextField()
    enc_date_field = fields.EncryptedDateField(null=True)
    enc_date_now_field = fields.EncryptedDateField(auto_now=True, null=True)
    enc_date_now_add_field = fields.EncryptedDateField(
        auto_now_add=True, null=True)
    enc_datetime_field = fields.EncryptedDateTimeField(null=True)
    enc_boolean_field = fields.EncryptedBooleanField(default=True)
    enc_integer_field = fields.EncryptedIntegerField(null=True)
    enc_positive_integer_field = fields.EncryptedPositiveIntegerField(
        null=True)
    enc_small_integer_field = fields.EncryptedSmallIntegerField(null=True)
    enc_positive_small_integer_field = fields.EncryptedPositiveSmallIntegerField(
        null=True)
    enc_big_integer_field = fields.EncryptedBigIntegerField(null=True)
    enc_ssn_field = fields.EncryptedSSNField(null=True, data_type_name='SSN')
