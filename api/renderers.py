from rest_framework_csv import renderers as r


class CSVRenderer(r.CSVStreamingRenderer):
    """
    Paginated renderer (when pagination is turned on for DRF)
    """

    results_field = "results"

    def render(self, data, *args, **kwargs):
        if not isinstance(data, list):
            data = data.get(self.results_field, [])
        return super(CSVRenderer, self).render(data, *args, **kwargs)
