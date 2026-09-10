from rest_framework.routers import DefaultRouter

from .views import CakeViewSet, OrderViewSet

router = DefaultRouter()
router.register(r"cakes", CakeViewSet, basename="cake")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = router.urls