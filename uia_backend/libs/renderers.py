from rest_framework.renderers import JSONRenderer


class CustomRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        status_code = renderer_context["response"].status_code
        response = {}

        if (
            isinstance(data, dict)
            and "count" in data.keys()
            and "next" in data.keys()
            and "previous" in data.keys()
            and "results" in data.keys()
        ):
            # mutate reponses with limit offset pagination
            count, _next, previous = (
                data.pop("count"),
                data.pop("next"),
                data.pop("previous"),
            )
            response = {"count": count, "next": _next, "previous": previous}
            data = data["results"]

        response.update(
            **{
                "status": "Success" if status_code in range(200, 300) else "Error",
                "code": status_code,
                "data": data,
            }
        )

        return super().render(response, accepted_media_type, renderer_context)
