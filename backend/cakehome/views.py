from django.db import connection
from django.http import JsonResponse
from rest_framework import viewsets

from .models import Cake
from .serializers import CakeSerializer

def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        database_ok = True
    except Exception:
        database_ok = False

    payload = {
        "status" : "ok" if database_ok else "degraded",
        "database" : database_ok,
    }

    return JsonResponse(payload, status=200 if database_ok else 503)

class CakeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cake.objects.select_related("category").filter(is_available=True)
    serializer_class = CakeSerializer





