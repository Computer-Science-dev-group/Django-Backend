from rest_framework.serializers import ModelSerializer


class DynamicFieldsModelSerializer(ModelSerializer):
    def __init__(self, *args, **kwargs):
        allowed_fields = kwargs.pop("allowed_fields", [])
        # instantaite the class normally
        super().__init__(*args, **kwargs)

        if allowed_fields:
            for field in set(self.fields).difference(allowed_fields):
                self.fields.pop(field)
