# management/commands/seed_heavy_machinery.py

import os
import pandas as pd
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

# Import your models - adjust the import path based on vehicles
from vehicles.models import HeavyMachineryMake, HeavyMachineryModel, HeavyMachinery


class Command(BaseCommand):
    help = 'Seeds Heavy Machinery data from Excel file (Tractors & Graders)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='for_machinery.xlsx',
            help='Path to the Excel file (default: for_machinery.xlsx)'
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default='Tractors & Graders July 2025',
            help='Sheet name in the Excel file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing heavy machinery data before importing'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the import without saving to database'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        sheet_name = options['sheet']
        clear_existing = options['clear']
        dry_run = options['dry_run']

        # Check if file exists
        if not os.path.exists(file_path):
            # Try looking in the project root or media directory
            alternate_paths = [
                os.path.join(settings.BASE_DIR, file_path),
                os.path.join(settings.MEDIA_ROOT, file_path) if hasattr(settings, 'MEDIA_ROOT') else None,
            ]

            file_found = False
            for alt_path in alternate_paths:
                if alt_path and os.path.exists(alt_path):
                    file_path = alt_path
                    file_found = True
                    break

            if not file_found:
                raise CommandError(f'File "{file_path}" does not exist.')

        self.stdout.write(f'Reading from: {file_path}')
        self.stdout.write(f'Sheet: {sheet_name}')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))

        try:
            # Read the Excel file
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Clean column names (remove extra spaces)
            df.columns = df.columns.str.strip()

            # Check required columns
            required_columns = ['MAKE', 'MODEL', 'HORSEPOWER', 'CRSP']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise CommandError(f'Missing required columns: {", ".join(missing_columns)}')

            # Clean the dataframe
            df = df.dropna(subset=['MAKE', 'MODEL', 'HORSEPOWER', 'CRSP'])

            # Convert columns to string and strip whitespace
            df['MAKE'] = df['MAKE'].astype(str).str.strip()
            df['MODEL'] = df['MODEL'].astype(str).str.strip()
            df['HORSEPOWER'] = df['HORSEPOWER'].astype(str).str.strip()

            total_rows = len(df)
            self.stdout.write(f'Found {total_rows} rows to process')

            if clear_existing and not dry_run:
                self.clear_existing_data()

            # Process the data
            success_count = 0
            error_count = 0
            skip_count = 0
            errors = []

            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        result = self.process_row(row, dry_run)
                        if result == 'success':
                            success_count += 1
                        elif result == 'skipped':
                            skip_count += 1
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Row {index + 2}: {str(e)}")
                        self.stdout.write(
                            self.style.ERROR(f'Error on row {index + 2}: {str(e)}')
                        )

                if dry_run:
                    transaction.set_rollback(True)

            # Print summary
            self.stdout.write(self.style.SUCCESS(f'\n{"="*50}'))
            self.stdout.write(self.style.SUCCESS('Import Summary:'))
            self.stdout.write(self.style.SUCCESS(f'{"="*50}'))
            self.stdout.write(f'Total rows processed: {total_rows}')
            self.stdout.write(self.style.SUCCESS(f'Successfully imported: {success_count}'))

            if skip_count > 0:
                self.stdout.write(self.style.WARNING(f'Skipped (duplicates): {skip_count}'))

            if error_count > 0:
                self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
                self.stdout.write(self.style.ERROR('\nError details:'))
                for error in errors[:10]:  # Show first 10 errors
                    self.stdout.write(self.style.ERROR(f'  - {error}'))
                if len(errors) > 10:
                    self.stdout.write(self.style.ERROR(f'  ... and {len(errors) - 10} more errors'))

            if dry_run:
                self.stdout.write(self.style.WARNING('\nDRY RUN COMPLETE - No data was saved'))
            else:
                self.stdout.write(self.style.SUCCESS('\nData import completed successfully!'))

        except FileNotFoundError:
            raise CommandError(f'File "{file_path}" not found.')
        except Exception as e:
            raise CommandError(f'Error reading Excel file: {str(e)}')

    def clear_existing_data(self):
        """Clear existing heavy machinery data"""
        self.stdout.write('Clearing existing data...')

        machinery_count = HeavyMachinery.objects.count()
        model_count = HeavyMachineryModel.objects.count()
        make_count = HeavyMachineryMake.objects.count()

        HeavyMachinery.objects.all().delete()
        HeavyMachineryModel.objects.all().delete()
        HeavyMachineryMake.objects.all().delete()

        self.stdout.write(
            self.style.WARNING(
                f'Deleted: {machinery_count} machinery, '
                f'{model_count} models, {make_count} makes'
            )
        )

    def process_row(self, row, dry_run=False):
        """Process a single row from the DataFrame"""
        make_name = row['MAKE']
        model_name = row['MODEL']
        horsepower = row['HORSEPOWER']
        crsp = row['CRSP']

        # Validate and clean CRSP value
        try:
            # Convert CRSP to Decimal
            if pd.isna(crsp):
                raise ValueError('CRSP value is missing')

            # Remove any non-numeric characters except decimal point
            crsp_str = str(crsp).replace(',', '').replace(' ', '').strip()

            # Convert to float first, then to int to remove decimals, then to Decimal
            # This handles Excel floating-point artifacts
            crsp_decimal = Decimal(int(float(crsp_str)))

            if crsp_decimal < 0:
                raise ValueError('CRSP cannot be negative')

        except (InvalidOperation, ValueError) as e:
            raise ValueError(f'Invalid CRSP value "{crsp}": {str(e)}')

        # Clean horsepower to remove .0 decimals
        try:
            hp_float = float(horsepower)
            if hp_float.is_integer():
                horsepower = str(int(hp_float))
            else:
                horsepower = str(hp_float)
        except (ValueError, TypeError):
            horsepower = str(horsepower).strip()

        if not dry_run:
            # Get or create Make
            make, make_created = HeavyMachineryMake.objects.get_or_create(
                name=make_name
            )

            # Get or create Model
            model, model_created = HeavyMachineryModel.objects.get_or_create(
                make=make,
                name=model_name
            )

            # Create or update Heavy Machinery
            machinery, created = HeavyMachinery.objects.update_or_create(
                make=make,
                model=model,
                horsepower=horsepower,
                defaults={
                    'crsp': crsp_decimal
                }
            )

            if created:
                self.stdout.write(
                    f'Created: {make_name} {model_name} - {horsepower} HP '
                    f'(KES {crsp_decimal:,})'
                )
                return 'success'
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Updated: {make_name} {model_name} - {horsepower} HP '
                        f'(KES {crsp_decimal:,})'
                    )
                )
                return 'skipped'
        else:
            # Dry run - just validate
            self.stdout.write(
                f'Would create: {make_name} {model_name} - {horsepower} HP '
                f'(KES {crsp_decimal:,})'
            )
            return 'success'


# Optional: Create a simpler function-based seeder for direct use
def seed_heavy_machinery_from_excel(file_path='for_machinery.xlsx',
                                    sheet_name='Tractors & Graders July 2025',
                                    clear_existing=False):
    """
    Utility function to seed heavy machinery data
    Can be called from Django shell or other scripts
    """
    import pandas as pd
    from decimal import Decimal

    if clear_existing:
        HeavyMachinery.objects.all().delete()
        HeavyMachineryModel.objects.all().delete()
        HeavyMachineryMake.objects.all().delete()
        print("Cleared existing data")

    df = pd.read_excel(file_path, sheet_name=sheet_name)
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['MAKE', 'MODEL', 'HORSEPOWER', 'CRSP'])

    success_count = 0
    error_count = 0

    for index, row in df.iterrows():
        try:
            make_name = str(row['MAKE']).strip()
            model_name = str(row['MODEL']).strip()

            # Clean horsepower
            hp_float = float(row['HORSEPOWER'])
            horsepower = str(int(hp_float)) if hp_float.is_integer() else str(hp_float)

            # Clean CRSP - convert to int to remove decimals
            crsp_value = str(row['CRSP']).replace(',', '').strip()
            crsp = Decimal(int(float(crsp_value)))

            # Get or create Make
            make, _ = HeavyMachineryMake.objects.get_or_create(name=make_name)

            # Get or create Model
            model, _ = HeavyMachineryModel.objects.get_or_create(
                make=make,
                name=model_name
            )

            # Create or update Heavy Machinery
            machinery, created = HeavyMachinery.objects.update_or_create(
                make=make,
                model=model,
                horsepower=horsepower,
                defaults={'crsp': crsp}
            )

            success_count += 1
            status = "Created" if created else "Updated"
            print(f"{status}: {make_name} {model_name} - {horsepower} HP (KES {crsp:,})")

        except Exception as e:
            error_count += 1
            print(f"Error on row {index + 2}: {str(e)}")

    print(f"\nCompleted: {success_count} successful, {error_count} errors")
    return success_count, error_count
