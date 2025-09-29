# calculator/management/commands/load_tax_rates.py
from django.core.management.base import BaseCommand
from calculator.models import DepreciationRate, VehicleCategory
from decimal import Decimal

class Command(BaseCommand):
    help = 'Load initial tax rates and depreciation data'

    def handle(self, *args, **kwargs):
        # Load Direct Import Depreciation Rates
        direct_rates = [
            (0, 1, 0),
            (1, 2, 20),
            (2, 3, 30),
            (3, 4, 40),
            (4, 5, 50),
            (5, 6, 55),
            (6, 7, 60),
            (7, 8, 65),
        ]

        for years_from, years_to, rate in direct_rates:
            DepreciationRate.objects.get_or_create(
                import_type='DIRECT',
                years_from=years_from,
                years_to=years_to,
                defaults={'depreciation_percentage': Decimal(str(rate))}
            )

        # Load Previously Registered Depreciation Rates
        prev_rates = [
            (0, 0, 0),
            (1, 1, 20),
            (2, 2, 35),
            (3, 3, 50),
            (4, 4, 60),
            (5, 5, 70),
            (6, 6, 75),
            (7, 7, 80),
            (8, 8, 83),
            (9, 9, 86),
            (10, 10, 89),
            (11, 11, 90),
            (12, 12, 91),
            (13, 13, 92),
            (14, 14, 93),
            (15, 15, 94),
            (16, 99, 95),  # Over 15 years
        ]

        for years_from, years_to, rate in prev_rates:
            DepreciationRate.objects.get_or_create(
                import_type='PREVIOUSLY_REGISTERED',
                years_from=years_from,
                years_to=years_to,
                defaults={'depreciation_percentage': Decimal(str(rate))}
            )

        # Load Vehicle Categories
        categories = [
            ('VEHICLE_1500CC_BELOW', 35, 20, None, 16, 42.6),
            ('VEHICLE_ABOVE_1500CC', 35, 25, None, 16, 40.9),
            ('VEHICLE_LUXURY', 35, 35, None, 16, 37.8),
            ('VEHICLE_ELECTRIC', 35, 10, None, 16, 46.4),
            ('SCHOOL_BUS', 35, 25, None, 16, 40.9),
            ('PRIME_MOVER', 35, 0, None, 16, 51.1),
            ('TRAILER', 35, 0, None, 16, 51.1),
            ('AMBULANCE', 0, 25, None, 16, 55.2),
            ('MOTORCYCLE', 25, None, 12952.83, 16, 55.2),
            ('SPECIAL_PURPOSE', 0, 0, None, 16, 69),
            ('HEAVY_MACHINERY', 0, 0, None, 16, 69),
        ]

        for cat, import_duty, excise_rate, excise_fixed, vat, customs_pct in categories:
            data = {
                'import_duty_rate': Decimal(str(import_duty)),
                'vat_rate': Decimal(str(vat)),
                'customs_value_percentage': Decimal(str(customs_pct))
            }

            if excise_rate is not None:
                data['excise_duty_rate'] = Decimal(str(excise_rate))

            if excise_fixed is not None:
                data['excise_duty_fixed'] = Decimal(str(excise_fixed))

            VehicleCategory.objects.get_or_create(
                category=cat,
                defaults=data
            )

        self.stdout.write(self.style.SUCCESS('Successfully loaded tax rates'))
