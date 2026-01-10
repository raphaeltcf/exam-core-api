from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, ParseError):
        return Response(
            {
                "detail": "JSON inválido.",
                "hint": "Verifique vírgulas, aspas e se o body é um objeto JSON.",
            },
            status=400,
        )
    return exception_handler(exc, context)

