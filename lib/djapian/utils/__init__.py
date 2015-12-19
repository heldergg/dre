from django.conf import settings
from django.apps import apps

DEFAULT_WEIGHT = 1

def model_name(model):
    return "%s.%s" % (model._meta.app_label, model._meta.object_name)

def load_indexes():
    from djapian.utils import loading
    for app_config in apps.get_app_configs():
        try:
            module = app_config.module.__name__
            loading.get_module(module, "index")
        except loading.NoModuleError:
            pass
