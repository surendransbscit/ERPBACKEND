from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.http import Http404

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        if isinstance(exc, ValidationError):
            # Process validation errors to a string format
            error_messages = []
            for field, errors in exc.detail.items():
                for error in errors:
                    error_messages.append(f"{field} Field is {error}")
            error_string = "; ".join(error_messages)
            response.data = {
                "status": False,
                "message": error_string
            }
        elif isinstance(exc, Http404):
            response.data = {
                "status": False,
                "message": "Not found"
            }
        else:
            response.data = {
                "status": False,
                "message": str(exc)
            }
            
    return response
