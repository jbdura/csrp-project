# management/commands/import_vehicle_spreadsheet.py
import pandas as pd
import numpy as np
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal, InvalidOperation
import re
from vehicles.models import (
    VehicleMake, VehicleModel, Vehicle,
    MotorcycleMake, MotorcycleModel, Motorcycle,
)

class Command(BaseCommand):
    help = 'Import all vehicle data from the master spreadsheet'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the Excel file')
        parser.add_argument('--clear', action='store_true',
                            help='Clear existing data before importing')

    def handle(self, *args, **options):
        file_path = options['file_path']

        if options['clear']:
            self.clear_existing_data()

        self.stdout.write(self.style.WARNING('Starting import from: ' + file_path))

        # Import each sheet
        self.import_vehicles(file_path)
        self.import_motorcycles(file_path)

        self.stdout.write(self.style.SUCCESS('Import completed successfully!'))

    def clear_existing_data(self):
        """Clear all existing vehicle data"""
        self.stdout.write(self.style.WARNING('Clearing existing data...'))
        Vehicle.objects.all().delete()
        VehicleModel.objects.all().delete()
        VehicleMake.objects.all().delete()

        Motorcycle.objects.all().delete()
        MotorcycleModel.objects.all().delete()
        MotorcycleMake.objects.all().delete()

        self.stdout.write(self.style.SUCCESS('Existing data cleared'))

    def clean_value(self, value):
        """Clean and standardize values"""
        if pd.isna(value) or value == '' or str(value).strip().upper() == 'N/A':
            return None
        if isinstance(value, str):
            val = value.strip()
            return val if val != '' else None
        return value

    def standardize_columns(self, df, aliases=None):
        """
        Normalize column names:
          - Trim
          - Replace any whitespace (incl. newlines) with underscore
          - Remove punctuation
          - Collapse multiple underscores
          - Lowercase
          - Apply alias mapping
        """
        new_cols = []
        for c in df.columns:
            name = str(c).strip()
            name = re.sub(r'\s+', '_', name)             # any whitespace -> _
            name = re.sub(r'[^0-9a-zA-Z_]', '', name)    # remove punctuation like ( ) . /
            name = re.sub(r'_+', '_', name).strip('_')   # collapse and trim underscores
            name = name.lower()
            new_cols.append(name)
        df.columns = new_cols

        # Aliases to unify the dataset
        aliases = aliases or {}
        # Always normalize common money header variations to 'crsp'
        if 'crsp_kes' in df.columns and 'crsp' not in df.columns:
            aliases['crsp_kes'] = 'crsp'
        if 'driveconfig' in df.columns and 'drive_configuration' not in df.columns:
            aliases['driveconfig'] = 'drive_configuration'
        if 'drivetrain' in df.columns and 'drive_configuration' not in df.columns:
            aliases['drivetrain'] = 'drive_configuration'
        if 'modelno' in df.columns and 'model_number' not in df.columns:
            aliases['modelno'] = 'model_number'
        if 'model_no' in df.columns and 'model_number' not in df.columns:
            aliases['model_no'] = 'model_number'
        if 'bodytype' in df.columns and 'body_type' not in df.columns:
            aliases['bodytype'] = 'body_type'

        if aliases:
            df.rename(columns=aliases, inplace=True)

        return df

    def parse_decimal(self, value, default=Decimal('0')):
        """
        Parse currency/number-like values to Decimal:
          - Handles strings with commas, spaces, currency text (KES, KSH), etc.
          - Handles numeric types
        """
        if value is None or (isinstance(value, float) and np.isnan(value)) or (isinstance(value, str) and value.strip() == ''):
            return default
        try:
            if isinstance(value, (int, float, np.integer, np.floating)):
                # Avoid float representation issues by converting through str
                return Decimal(str(value))
            s = str(value)
            # remove anything that's not digit/sign/dot
            s = re.sub(r'[^0-9\.\-]', '', s)
            if s == '' or s == '-' or s == '.':
                return default
            return Decimal(s)
        except (InvalidOperation, ValueError, TypeError):
            return default

    def parse_int(self, value, default=None):
        """
        Parse seating-like values: supports numeric strings and strings like '5 seater', '2 PAX'
        """
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return default
        if isinstance(value, (int, np.integer)):
            return int(value)
        s = str(value).strip()
        m = re.search(r'\d+', s)
        if m:
            try:
                return int(m.group(0))
            except Exception:
                return default
        return default

    def to_str_or_none(self, value):
        """
        Turn a value into a reasonable string or None.
        Avoids str(None) -> 'None'. Also cleans floats that are integer-like.
        """
        val = self.clean_value(value)
        if val is None:
            return None
        if isinstance(val, float):
            if np.isnan(val):
                return None
            if float(int(val)) == val:
                return str(int(val))
        return str(val)

    def normalize_transmission(self, trans_value, vehicle_type='vehicle'):
        """Normalize transmission values to match model choices"""
        if pd.isna(trans_value) or trans_value == '':
            return None

        trans_value = str(trans_value).upper().strip()

        if vehicle_type == 'vehicle':
            mapping = {
                'AUTOMATIC': 'AT',
                'AUTO': 'AT',
                'AT': 'AT',
                'MANUAL': 'MT',
                'MT': 'MT',
                'CVT': 'CVT',
                'AMT': 'AMT',
                'AUTOMATED MANUAL': 'AMT',
            }
        else:  # motorcycle
            mapping = {
                '3-SPEED': '3MT',
                '3MT': '3MT',
                '4-SPEED': '4MT',
                '4MT': '4MT',
                '5-SPEED': '5MT',
                '5MT': '5MT',
                '6-SPEED': '6MT',
                '6MT': '6MT',
                'CVT': 'CVT',
                'DCT': 'DCT',
                'AUTO': 'AUTO',
                'AUTOMATIC': 'AUTO',
                'NONE': 'NONE',
                'ELECTRIC': 'NONE',
            }

        return mapping.get(trans_value, trans_value if len(trans_value) <= 10 else None)

    def normalize_drive_config(self, drive_value):
        """Normalize drive configuration values"""
        if pd.isna(drive_value) or drive_value == '':
            return 'FWD'  # Default value

        drive_value = str(drive_value).upper().strip()
        mapping = {
            'FRONT WHEEL DRIVE': 'FWD',
            'FWD': 'FWD',
            'REAR WHEEL DRIVE': 'RWD',
            'RWD': 'RWD',
            'FOUR WHEEL DRIVE': '4WD',
            '4WD': '4WD',
            'ALL WHEEL DRIVE': 'AWD',
            'AWD': 'AWD',
            'TWO WHEEL DRIVE': '2WD',
            '2WD': '2WD',
        }
        return mapping.get(drive_value, 'FWD')

    def normalize_body_type(self, body_value):
        """Normalize body type values"""
        if pd.isna(body_value) or body_value == '':
            return 'SEDAN'  # Default value

        body_value = str(body_value).upper().strip()
        mapping = {
            'SUV': 'SUV',
            'SEDAN': 'SEDAN',
            'SALOON': 'SEDAN',
            'HATCHBACK': 'HATCHBACK',
            'HATCH': 'HATCHBACK',
            'WAGON': 'WAGON',
            'STATION WAGON': 'S.WAGON',
            'S.WAGON': 'S.WAGON',
            'COUPE': 'COUPE',
            'CONVERTIBLE': 'CONVERTIBLE',
            'VAN': 'VAN',
            'TRUCK': 'TRUCK',
            'PICKUP': 'PICKUP',
            'PICK UP': 'PICKUP',
        }
        return mapping.get(body_value, 'SEDAN')

    def normalize_fuel_type(self, fuel_value, vehicle_type='vehicle'):
        """Normalize fuel type values"""
        if pd.isna(fuel_value) or fuel_value == '':
            return 'GASOLINE'  # Default value

        fuel_value = str(fuel_value).upper().strip()

        if vehicle_type == 'motorcycle':
            mapping = {
                'GASOLINE': 'GASOLINE',
                'PETROL': 'GASOLINE',
                'GAS': 'GASOLINE',
                'ELECTRIC': 'ELECTRIC',
                'EV': 'ELECTRIC',
            }
            return mapping.get(fuel_value, 'GASOLINE')
        else:
            mapping = {
                'GASOLINE': 'GASOLINE',
                'GAS': 'GASOLINE',
                'DIESEL': 'DIESEL',
                'ELECTRIC': 'ELECTRIC',
                'EV': 'ELECTRIC',
                'HYBRID': 'HYBRID',
                'PLUG-IN HYBRID': 'PLUG-IN HYBRID',
                'PLUGIN HYBRID': 'PLUG-IN HYBRID',
                'PHEV': 'PLUG-IN HYBRID',
                'PETROL': 'PETROL',
            }
            return mapping.get(fuel_value, 'GASOLINE')

    @transaction.atomic
    def import_vehicles(self, file_path):
        """Import vehicles from M.Vehicle CRSP July 2025 sheet"""
        self.stdout.write(self.style.WARNING('Importing vehicles...'))

        try:
            df = pd.read_excel(file_path, sheet_name='M.Vehicle CRSP July 2025')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading vehicles sheet: {str(e)}'))
            return

        # Clean column names (handles newlines, punctuation) and unify key aliases
        df = self.standardize_columns(df, aliases={
            # explicitly ensure our expected keys exist
            'crsp_kes': 'crsp',
            'driveconfig': 'drive_configuration',
            'modelno': 'model_number',
            'model_no': 'model_number',
            'bodytype': 'body_type',
        })

        created_count = 0
        skipped_count = 0
        error_count = 0

        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row.get('make')) or pd.isna(row.get('model')):
                    continue

                # Get or create make
                make_name = self.clean_value(row['make'])
                if not make_name:
                    continue

                make, _ = VehicleMake.objects.get_or_create(
                    name=make_name.upper()
                )

                # Get or create model
                model_name = self.clean_value(row['model'])
                if not model_name:
                    continue

                model_number = self.to_str_or_none(row.get('model_number'))

                vehicle_model, created_vm = VehicleModel.objects.get_or_create(
                    make=make,
                    name=model_name,
                    defaults={'model_number': model_number}
                )
                # Optional: update model_number if empty on existing record
                if not created_vm and model_number and not vehicle_model.model_number:
                    vehicle_model.model_number = model_number
                    vehicle_model.save(update_fields=['model_number'])

                # Prepare vehicle data
                engine_capacity = self.to_str_or_none(row.get('engine_capacity'))
                body_type = self.normalize_body_type(row.get('body_type'))
                drive_conf = self.normalize_drive_config(
                    row.get('drive_configuration', row.get('drive_config'))
                )
                seating = self.parse_int(row.get('seating'), default=None)
                fuel_in = row.get('fuel_type', row.get('fuel'))
                fuel_type = self.normalize_fuel_type(fuel_in, 'vehicle')
                crsp = self.parse_decimal(row.get('crsp'), default=Decimal('0'))

                vehicle_data = {
                    'make': make,
                    'model': vehicle_model,
                    'model_number': model_number,
                    'transmission': self.normalize_transmission(row.get('transmission')),
                    'drive_configuration': drive_conf,
                    'engine_capacity': engine_capacity,
                    'body_type': body_type,
                    'gvw': self.clean_value(row.get('gvw')),
                    'seating': seating,
                    'fuel_type': fuel_type,
                    'crsp': crsp,
                }

                # Check for existing vehicle
                exists = Vehicle.objects.filter(
                    make=make,
                    model=vehicle_model,
                    model_number=vehicle_data['model_number'],
                    transmission=vehicle_data['transmission'],
                    drive_configuration=vehicle_data['drive_configuration']
                ).exists()

                if not exists:
                    Vehicle.objects.create(**vehicle_data)
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'Error on row {index + 2}: {str(e)}'
                ))
                continue

        self.stdout.write(self.style.SUCCESS(
            f'Vehicles: Created {created_count}, Skipped {skipped_count}, Errors {error_count}'
        ))

    @transaction.atomic
    def import_motorcycles(self, file_path):
        """Import motorcycles from Motor Cycles July 2025 sheet"""
        self.stdout.write(self.style.WARNING('Importing motorcycles...'))

        try:
            df = pd.read_excel(file_path, sheet_name='Motor Cycles July 2025')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading motorcycles sheet: {str(e)}'))
            return

        # Clean column names (handles newlines, punctuation) and unify key aliases
        df = self.standardize_columns(df, aliases={
            'crsp_kes': 'crsp',
            'modelno': 'model_number',
            'model_no': 'model_number',
        })

        created_count = 0
        skipped_count = 0
        error_count = 0

        for index, row in df.iterrows():
            try:
                # Skip empty rows
                if pd.isna(row.get('make')) or pd.isna(row.get('model')):
                    continue

                # Get or create make
                make_name = self.clean_value(row['make'])
                if not make_name:
                    continue

                make, _ = MotorcycleMake.objects.get_or_create(
                    name=make_name.upper()
                )

                # Get or create model
                model_name = self.clean_value(row['model'])
                if not model_name:
                    continue

                model_number = self.to_str_or_none(row.get('model_number'))

                motorcycle_model, created_mm = MotorcycleModel.objects.get_or_create(
                    make=make,
                    name=model_name,
                    defaults={'model_number': model_number}
                )
                # Optional: update model_number if empty on existing record
                if not created_mm and model_number and not motorcycle_model.model_number:
                    motorcycle_model.model_number = model_number
                    motorcycle_model.save(update_fields=['model_number'])

                # Prepare motorcycle data
                transmission = self.normalize_transmission(row.get('transmission'), 'motorcycle')
                engine_capacity = self.to_str_or_none(row.get('engine_capacity'))
                seating = self.parse_int(row.get('seating'), default=2)
                fuel = self.normalize_fuel_type(row.get('fuel', row.get('fuel_type')), 'motorcycle')
                crsp = self.parse_decimal(row.get('crsp'), default=Decimal('0'))

                motorcycle_data = {
                    'make': make,
                    'model': motorcycle_model,
                    'model_number': model_number,
                    'transmission': transmission,
                    'engine_capacity': engine_capacity,
                    'seating': seating,
                    'fuel': fuel,
                    'crsp': crsp,
                }

                # Check for existing motorcycle
                exists = Motorcycle.objects.filter(
                    make=make,
                    model=motorcycle_model,
                    model_number=motorcycle_data['model_number'],
                    transmission=motorcycle_data['transmission'],
                    engine_capacity=motorcycle_data['engine_capacity']
                ).exists()

                if not exists:
                    Motorcycle.objects.create(**motorcycle_data)
                    created_count += 1
                else:
                    skipped_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(
                    f'Error on row {index + 2}: {str(e)}'
                ))
                continue

        self.stdout.write(self.style.SUCCESS(
            f'Motorcycles: Created {created_count}, Skipped {skipped_count}, Errors {error_count}'
        ))
