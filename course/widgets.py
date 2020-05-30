from django.forms import RadioSelect


class RadioInlineSelect(RadioSelect):
    template_name = 'widgets/radio_inline.html'
    option_template_name = 'widgets/radio_inline_option.html'

    def __init__(self, attr=None, choices=()):
        super().__init__(attr, choices)
