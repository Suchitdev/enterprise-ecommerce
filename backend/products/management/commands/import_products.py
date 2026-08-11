import json
from pathlib import Path

from django.core.management.base import BaseCommand

from products.models import Category, Product


class Command(BaseCommand):
    help = "Import products from products.json"

    def handle(self, *args, **kwargs):

        json_file = (
            Path(__file__)
            .resolve()
            .parents[2]
            / "data"
            / "products.json"
        )

        with open(json_file, "r", encoding="utf-8") as file:
            products = json.load(file)

        count = 0

        for item in products:

            category, _ = Category.objects.get_or_create(
                name=item["category"],
                defaults={
                    "slug": item["category"].lower().replace(" ", "-")
                }
            )

            Product.objects.update_or_create(
                sku=item["sku"],
                defaults={
                    "category": category,
                    "name": item["name"],
                    "slug": item["slug"],
                    "description": item["description"],
                    "brand": item["brand"],
                    "price": item["price"],
                    "discount_price": item["discount_price"],
                    "stock": item["stock"],
                    "image": item["image"],
                    "is_available": True,
                },
            )

            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} products imported successfully!"
            )
        )