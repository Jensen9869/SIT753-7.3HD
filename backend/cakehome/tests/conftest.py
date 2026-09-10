from decimal import Decimal

import pytest

from cakehome.models import Cake, Category


@pytest.fixture
def category(db):
    return Category.objects.create(name="Sponge", slug="sponge")


@pytest.fixture
def cake(category):
    return Cake.objects.create(
        name="Vanilla Sponge",
        description="Classic vanilla",
        price=Decimal("40.00"),
        category=category,
        stock=10,
        is_available=True,
    )


@pytest.fixture
def sold_out_cake(category):
    return Cake.objects.create(
        name="Lemon Tart",
        price=Decimal("35.00"),
        category=category,
        stock=0,
        is_available=True,
    )