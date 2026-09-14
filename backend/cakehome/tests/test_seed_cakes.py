# backend/cakehome/tests/test_seed_cakes.py
import pytest
from django.core.management import call_command

from cakehome.models import Cake, Category


@pytest.mark.django_db
class TestSeedCakes:
    def test_creates_categories_and_cakes(self):
        call_command("seed_cakes")          
        assert Category.objects.count() == 3
        assert Cake.objects.count() == 4

    def test_running_twice_does_not_duplicate(self):
        call_command("seed_cakes")
        call_command("seed_cakes")          
        assert Cake.objects.count() == 4