from rest_framework.renderers import JSONRenderer


class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context["response"].status_code

        response = {
            "status": "Success" if status_code in range(200, 300) else "Error",
            "code": status_code,
            "data": data,
        }

        return super().render(response, accepted_media_type, renderer_context)
