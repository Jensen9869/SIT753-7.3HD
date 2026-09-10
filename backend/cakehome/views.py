from django.db import connection
from django.http import JsonResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Cake, Order
from .ordering import OrderError, place_order
from .serializers import CakeSerializer, OrderCreateSerializer, OrderSerializer


def health(request):
    """
    Liveness and readiness probe.

    Docker's HEALTHCHECK and the Jenkins deploy stages both poll this, so it
    stays cheap but does actually touch the database.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        database_ok = True
    except Exception:
        database_ok = False

    payload = {
        "status": "ok" if database_ok else "degraded",
        "database": database_ok,
    }
    return JsonResponse(payload, status=200 if database_ok else 503)


class CakeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Cake.objects.select_related("category").filter(is_available=True)
    serializer_class = CakeSerializer


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Order.objects.prefetch_related("items__cake")
    serializer_class = OrderSerializer

    def create(self, request):
        """Place a new order."""
        form = OrderCreateSerializer(data=request.data)
        form.is_valid(raise_exception=True)

        try:
            order = place_order(**form.validated_data)
        except OrderError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def advance(self, request, pk=None):
        """Move an order to the next status."""
        order = self.get_object()
        target = request.data.get("status")

        if not target:
            return Response({"error": "status is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            order.transition_to(target)
        except ValueError as exc:
            return Response({"error": str(exc)},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(OrderSerializer(order).data)



