from rest_framework.routers import DefaultRouter

from .views import CakeViewSet

router = DefaultRouter()
router.register(r"cakes", CakeViewSet, basename="cake")

urlpatterns = router.urls