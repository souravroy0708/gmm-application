from django.core.management.base import BaseCommand

from apps.catalog.sample_data import fill_products


class Command(BaseCommand):
    help = (
        "Fill the 5 launch products with sample Bengali names, descriptions, prices, GST/HSN, weights, stock "
        "and photos. Only empty/zero fields are filled unless --force is given. Sample values - confirm before launch."
    )

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Overwrite values that are already filled.")

    def handle(self, *args, **opts):
        n = fill_products(force=opts["force"])
        self.stdout.write(self.style.SUCCESS(f"Sample details filled for {n} product(s)."))
