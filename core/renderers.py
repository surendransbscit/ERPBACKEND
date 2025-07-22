from rest_framework.renderers import JSONRenderer
import json
from decimal import Decimal

class DecimalWithPrecision:
    def __init__(self, value: Decimal, precision: int = 2):
        self.value = value
        self.precision = precision

class CustomJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        def decimal_encoder(obj):
            if isinstance(obj, DecimalWithPrecision):
                return format(obj.value, f".{obj.precision}f")
            elif isinstance(obj, Decimal):
                return format(obj, ".2f")  # default fallback
            return obj
        return json.dumps(data, default=decimal_encoder).encode("utf-8")
