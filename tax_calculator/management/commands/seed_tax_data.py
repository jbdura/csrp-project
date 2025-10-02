from django.core.management.base import BaseCommand
from decimal import Decimal
from datetime import date
from tax_calculator.models import VehicleCategory, DepreciationRate, TaxConfiguration


class Command(BaseCommand):
    help = 'Seed initial tax calculation data based on KRA 2025 rates'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Starting to seed tax data...'))

        # Create tax configuration
        self.stdout.write('Creating tax configuration...')
        config, created = TaxConfiguration.objects.get_or_create(
            id=1,
            defaults={
                'vat_rate': Decimal('16.00'),
                'idf_rate': Decimal('3.500'),
                'rdl_rate': Decimal('2.000'),
                'current_year': 2025,
                'estimated_clearing_agent_fee': Decimal('20000.00'),
                'estimated_port_handling': Decimal('15000.00'),
                'estimated_ntsa_inspection': Decimal('5000.00'),
                'estimated_registration': Decimal('20000.00'),
                'estimated_transport': Decimal('25000.00'),
                'effective_from': date(2025, 1, 1),
                'is_active': True,
                'notes': 'Initial KRA tax configuration for 2025'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('✓ Tax configuration created'))
        else:
            self.stdout.write(self.style.WARNING('⚠ Tax configuration already exists'))

        # Create vehicle categories
        self.stdout.write('\nCreating vehicle categories...')
        categories = [
            {
                'name': 'Passenger Car ≤1500cc',
                'category_type': 'PASSENGER_CAR_SMALL',
                'description': 'Small passenger cars with engine capacity not exceeding 1500cc',
                'customs_factor': Decimal('0.426'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('20.00'),
            },
            {
                'name': 'Passenger Car >1500cc',
                'category_type': 'PASSENGER_CAR_MEDIUM',
                'description': 'Medium passenger cars with engine capacity exceeding 1500cc',
                'customs_factor': Decimal('0.409'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('25.00'),
            },
            {
                'name': 'Passenger Car >3000cc petrol / >2500cc diesel',
                'category_type': 'PASSENGER_CAR_LARGE',
                'description': 'Large engine passenger cars (HS 8703.24.90 & 8703.33.90)',
                'customs_factor': Decimal('0.378'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('35.00'),
                'hs_codes': '8703.24.90, 8703.33.90',
            },
            {
                'name': '100% Electric Vehicle',
                'category_type': 'ELECTRIC_VEHICLE',
                'description': '100% electric powered vehicles for transportation',
                'customs_factor': Decimal('0.464'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('10.00'),
                'hs_codes': '8702.40.11, 8702.40.19, 8702.40.21, 8702.40.22, 8702.40.29, 8702.40.91, 8702.40.99, 8703.80.00',
            },
            {
                'name': 'Hybrid Vehicle',
                'category_type': 'HYBRID_VEHICLE',
                'description': 'Hybrid vehicles (petrol/diesel + electric)',
                'customs_factor': Decimal('0.409'),
                'import_duty_rate': Decimal('25.00'),
                'excise_duty_rate': Decimal('20.00'),
            },
            {
                'name': 'Bus',
                'category_type': 'BUS',
                'description': 'Buses and coaches',
                'customs_factor': Decimal('0.409'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('25.00'),
                'hs_codes': '8702',
            },
            {
                'name': 'School Bus (Public Schools)',
                'category_type': 'SCHOOL_BUS',
                'description': 'School buses for public schools',
                'customs_factor': Decimal('0.409'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('25.00'),
            },
            {
                'name': 'Truck/Lorry',
                'category_type': 'TRUCK',
                'description': 'Trucks and lorries',
                'customs_factor': Decimal('0.409'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('25.00'),
                'hs_codes': '8704',
            },
            {
                'name': 'Prime Mover',
                'category_type': 'PRIME_MOVER',
                'description': 'Prime movers (no excise duty)',
                'customs_factor': Decimal('0.511'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('0.00'),
                'exempt_excise_duty': True,
            },
            {
                'name': 'Trailer',
                'category_type': 'TRAILER',
                'description': 'Trailers (no excise duty)',
                'customs_factor': Decimal('0.511'),
                'import_duty_rate': Decimal('35.00'),
                'excise_duty_rate': Decimal('0.00'),
                'exempt_excise_duty': True,
            },
            {
                'name': 'Ambulance',
                'category_type': 'AMBULANCE',
                'description': 'Ambulances (import duty exempt)',
                'customs_factor': Decimal('0.552'),
                'import_duty_rate': Decimal('0.00'),
                'excise_duty_rate': Decimal('25.00'),
                'exempt_import_duty': True,
            },
            {
                'name': 'Motorcycle',
                'category_type': 'MOTORCYCLE',
                'description': 'Motorcycles (fixed excise duty)',
                'customs_factor': Decimal('0.552'),
                'import_duty_rate': Decimal('25.00'),
                'excise_duty_rate': None,
                'excise_duty_fixed_amount': Decimal('12953.00'),
            },
            {
                'name': 'Special Purpose Vehicle',
                'category_type': 'SPECIAL_PURPOSE',
                'description': 'Special purpose vehicles (tax exempt)',
                'customs_factor': Decimal('0.690'),
                'import_duty_rate': Decimal('0.00'),
                'excise_duty_rate': Decimal('0.00'),
                'exempt_import_duty': True,
                'exempt_excise_duty': True,
            },
            {
                'name': 'Heavy Machinery',
                'category_type': 'HEAVY_MACHINERY',
                'description': 'Heavy machinery and equipment (tax exempt)',
                'customs_factor': Decimal('0.690'),
                'import_duty_rate': Decimal('0.00'),
                'excise_duty_rate': Decimal('0.00'),
                'exempt_import_duty': True,
                'exempt_excise_duty': True,
            },
        ]

        for cat_data in categories:
            category, created = VehicleCategory.objects.get_or_create(
                category_type=cat_data['category_type'],
                defaults={
                    **cat_data,
                    'effective_from': date(2025, 1, 1),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ Already exists: {category.name}'))

        # Create depreciation rates for DIRECT imports
        self.stdout.write('\nCreating depreciation rates for DIRECT imports...')
        direct_rates = [
            (1, 20), (2, 30), (3, 40), (4, 50),
            (5, 55), (6, 60), (7, 65), (8, 65),
        ]

        for age, rate in direct_rates:
            dep_rate, created = DepreciationRate.objects.get_or_create(
                import_type='DIRECT',
                vehicle_age_years=age,
                effective_from=date(2025, 1, 1),
                defaults={
                    'depreciation_rate': Decimal(str(rate)),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Direct Import - {age} years: {rate}%'))

        # Create depreciation rates for PREVIOUSLY_REGISTERED
        self.stdout.write('\nCreating depreciation rates for PREVIOUSLY REGISTERED...')
        prev_reg_rates = [
            (1, 20), (2, 35), (3, 50), (4, 60), (5, 70),
            (6, 75), (7, 80), (8, 83), (9, 86), (10, 89),
            (11, 90), (12, 91), (13, 92), (14, 93), (15, 94),
            (16, 95), (17, 95), (18, 95), (19, 95), (20, 95),
        ]

        for age, rate in prev_reg_rates:
            dep_rate, created = DepreciationRate.objects.get_or_create(
                import_type='PREVIOUSLY_REGISTERED',
                vehicle_age_years=age,
                effective_from=date(2025, 1, 1),
                defaults={
                    'depreciation_rate': Decimal(str(rate)),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Previously Registered - {age} years: {rate}%'))

        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Tax data seeded successfully! ✓'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write('\nYou can now:')
        self.stdout.write('1. Access admin panel to manage rates')
        self.stdout.write('2. Use the API endpoints to calculate taxes')
        self.stdout.write('3. Update rates when KRA changes them\n')
