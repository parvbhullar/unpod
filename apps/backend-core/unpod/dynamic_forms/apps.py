from django.apps import AppConfig


class DynamicFormConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'unpod.dynamic_forms'
    verbose_name = 'Dynamic Forms'
