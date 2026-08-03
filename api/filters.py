import warnings

from django_filters.rest_framework import DjangoFilterBackend as BaseDjangoFilterBackend


class DjangoFilterBackend(BaseDjangoFilterBackend):
    """``DjangoFilterBackend`` with DRF's OpenAPI hook restored.

    django-filter dropped ``get_schema_operation_parameters()`` from its DRF backend, but
    ``rest_framework.schemas.openapi`` still calls it on every filter backend, so
    ``/api/openapi`` raises ``AttributeError`` without it.  The implementation below is the
    one django-filter used to ship, so the generated schema is unchanged.
    """

    def get_schema_operation_parameters(self, view):
        try:
            queryset = view.get_queryset()
        except Exception:
            queryset = None
            warnings.warn("{} is not compatible with schema generation".format(view.__class__))

        filterset_class = self.get_filterset_class(view, queryset)

        if not filterset_class:
            return []

        parameters = []
        for field_name, field in filterset_class.base_filters.items():
            parameter = {
                "name": field_name,
                "required": field.extra["required"],
                "in": "query",
                "description": field.label if field.label is not None else field_name,
                "schema": {
                    "type": "string",
                },
            }
            if field.extra and "choices" in field.extra:
                parameter["schema"]["enum"] = [c[0] for c in field.extra["choices"]]
            parameters.append(parameter)
        return parameters
