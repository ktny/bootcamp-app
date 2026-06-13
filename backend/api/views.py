from django.http import JsonResponse


def hello(_request):
    return JsonResponse({"message": "Hello, world!"})
