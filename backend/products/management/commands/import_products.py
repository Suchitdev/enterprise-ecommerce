import json
from pathlib import Path
from urllib.request import Request, urlopen
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.models import Category, Product


class Command(BaseCommand):
    help = "Import products from local JSON or DummyJSON API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            choices=["local", "api"],
            default="local",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
        )

    def handle(self, *args, **kwargs):
        source = kwargs["source"]
        limit = kwargs["limit"]

        if source == "local":
            products = self.load_local_products()
        else:
            products = self.load_api_products(limit)

        count = 0

        for item in products:
            category_name = item["category"].replace("-", " ").title()

            category, _ = Category.objects.get_or_create(
                name=category_name,
                defaults={
                    "slug": slugify(category_name)
                },
            )

            price = Decimal(str(item["price"]))

            discount_percentage = Decimal(
                str(item.get("discountPercentage", 0))
            )

            discount_price = (
                price
                * (Decimal("1") - discount_percentage / Decimal("100"))
            ).quantize(Decimal("0.01"))

            sku = item.get("sku") or f"API-{item['id']}"

            Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "category": category,
                    "name": item.get(
                        "title",
                        item.get("name", "Product")
                    ),
                    "slug": slugify(
                        f"{item.get('title', item.get('name', 'Product'))}-{sku}"
                    ),
                    "description": item.get("description", ""),
                    "brand": item.get("brand") or "Generic",
                    "price": price,
                    "discount_price": discount_price,
                    "stock": item.get("stock", 0),
                    "image": item.get("thumbnail")
                    or (
                        item.get("images", [None])[0]
                        if item.get("images")
                        else None
                    ),
                    "is_available": True,
                },
            )

            count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} products imported successfully!"
            )
        )

    def load_local_products(self):
        json_file = (
            Path(__file__)
            .resolve()
            .parents[2]
            / "data"
            / "products.json"
        )

        with open(json_file, "r", encoding="utf-8") as file:
            return json.load(file)

    def load_api_products(self, limit):
        url = f"https://dummyjson.com/products?limit={limit}"

        request = Request(
            url,
            headers={
                "User-Agent": "enterprise-ecommerce-importer"
            },
        )

        with urlopen(request, timeout=30) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        return data["products"]
