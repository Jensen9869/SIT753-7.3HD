"""Put a few cakes on the board so a fresh environment has something to show."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from cakehome.models import Cake, Category

CATEGORIES = [
    ("Sponge", "sponge"),
    ("Tart", "tart"),
    ("Cheesecake", "cheesecake"),
]

CAKES = [
    ("Vanilla bean sponge",
     "Two layers, vanilla bean cream, a little raspberry jam.",
     "42.00", "sponge", 8),
    ("Burnt Basque cheesecake",
     "Caramelised on top, barely set in the middle.",
     "48.00", "cheesecake", 5),
    ("Lemon and thyme tart",
     "Sharp curd in a short crust, thyme from the garden.",
     "38.00", "tart", 2),
    ("Chocolate and olive oil",
     "Flourless, olive oil and sea salt.",
     "52.00", "sponge", 6),
]


class Command(BaseCommand):
    help = "Create the starting set of categories and cakes."

    def handle(self, *args, **options):
        for name, slug in CATEGORIES:
            Category.objects.get_or_create(slug=slug, defaults={"name": name})

        created = 0
        for name, description, price, slug, stock in CAKES:
            _, was_created = Cake.objects.get_or_create(
                name=name,
                defaults={
                    "description": description,
                    "price": Decimal(price),
                    "category": Category.objects.get(slug=slug),
                    "stock": stock,
                },
            )
            created += was_created

        self.stdout.write(self.style.SUCCESS(
            f"{created} cakes added, {Cake.objects.count()} on the board."
        ))