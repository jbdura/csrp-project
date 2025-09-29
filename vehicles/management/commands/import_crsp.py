import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from decimal import Decimal, InvalidOperation
from vehicles.models import (
    VehicleMake, VehicleModel, Vehicle,
    MotorcycleMake, MotorcycleModel, Motorcycle
)
import os

class Command(BaseCommand):
    help = 'Populate vehicle and motorcycle data from CRSP.xlsx'

    def add_arguments(self, parser):
        parser.add_argument(
            'excel_file',
            type=str,
            help='Path to the CRSP.xlsx file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing',
        )

    def handle(self, *args, **options):
        excel_file = options['excel_file']

        if not os.path.exists(excel_file):
            raise CommandError(f'Excel file "{excel_file}" does not exist.')

        try:
            # Read the Excel file
            self.stdout.write('Reading Excel file...')
            vehicles_df = pd.read_excel(excel_file, sheet_name='M.Vehicle CRSP July 2025')
            motorcycles_df = pd.read_excel(excel_file, sheet_name='Motor Cycles July 2025')

            if options['clear']:
                self.stdout.write('Clearing existing data...')
                self.clear_existing_data()

            # Process vehicles
            self.stdout.write('Processing vehicles...')
            self.process_vehicles(vehicles_df)

            # Process motorcycles
            self.stdout.write('Processing motorcycles...')
            self.process_motorcycles(motorcycles_df)

            self.stdout.write(
                self.style.SUCCESS('Successfully populated database from Excel file.')
            )

        except Exception as e:
            raise CommandError(f'Error processing Excel file: {str(e)}')

    def clear_existing_data(self):
        """Clear existing vehicle and motorcycle data"""
        Vehicle.objects.all().delete()
        VehicleModel.objects.all().delete()
        VehicleMake.objects.all().delete()
        Motorcycle.objects.all().delete()
        MotorcycleModel.objects.all().delete()
        MotorcycleMake.objects.all().delete()

    def clean_string(self, value):
        """Clean and normalize string values"""
        if pd.isna(value) or value is None:
            return None
        return str(value).strip()

    def clean_decimal(self, value):
        """Clean and convert decimal values"""
        if pd.isna(value) or value is None:
            return None

        # Handle string values that might have commas or currency symbols
        if isinstance(value, str):
            # Remove common currency symbols and commas
            cleaned = value.replace('KES', '').replace(',', '').replace(' ', '').strip()
            if not cleaned:
                return None
            try:
                return Decimal(cleaned)
            except (InvalidOperation, ValueError):
                return None

        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None

    def clean_integer(self, value):
        """Clean and convert integer values"""
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def map_transmission(self, transmission_value, is_motorcycle=False):
        """Map transmission values to model choices"""
        if pd.isna(transmission_value) or transmission_value is None:
            return None

        transmission = str(transmission_value).strip().upper()

        if is_motorcycle:
            # Motorcycle transmission mapping
            mapping = {
                '3MT': '3MT',
                '4MT': '4MT',
                '5MT': '5MT',
                '6MT': '6MT',
                'CVT': 'CVT',
                'DCT': 'DCT',
                'AUTO': 'AUTO',
                'AUTOMATIC': 'AUTO',
                'NONE': 'NONE',
                'NO GEARS': 'NONE',
                'ELECTRIC': 'NONE',
            }
        else:
            # Vehicle transmission mapping
            mapping = {
                'AT': 'AT',
                'AUTO': 'AT',
                'AUTOMATIC': 'AT',
                'MT': 'MT',
                'MANUAL': 'MT',
                'CVT': 'CVT',
                'AMT': 'AMT',
                'AUTOMATED MANUAL': 'AMT',
            }

        return mapping.get(transmission, transmission if not is_motorcycle else None)

    def map_drive_configuration(self, drive_config):
        """Map drive configuration values to model choices"""
        if pd.isna(drive_config) or drive_config is None:
            return None

        config = str(drive_config).strip().upper()
        mapping = {
            'FWD': 'FWD',
            'FRONT WHEEL DRIVE': 'FWD',
            'RWD': 'RWD',
            'REAR WHEEL DRIVE': 'RWD',
            '4WD': '4WD',
            'FOUR WHEEL DRIVE': '4WD',
            'AWD': 'AWD',
            'ALL WHEEL DRIVE': 'AWD',
            '2WD': '2WD',
            'TWO WHEEL DRIVE': '2WD',
        }
        return mapping.get(config, config)

    def map_body_type(self, body_type):
        """Map body type values to model choices"""
        if pd.isna(body_type) or body_type is None:
            return None

        body = str(body_type).strip().upper()
        mapping = {
            'SUV': 'SUV',
            'SEDAN': 'SEDAN',
            'HATCHBACK': 'HATCHBACK',
            'WAGON': 'WAGON',
            'S.WAGON': 'S.WAGON',
            'STATION WAGON': 'S.WAGON',
            'COUPE': 'COUPE',
            'CONVERTIBLE': 'CONVERTIBLE',
            'VAN': 'VAN',
            'TRUCK': 'TRUCK',
            'PICKUP': 'PICKUP',
        }
        return mapping.get(body, body)

    def map_fuel_type(self, fuel_type, is_motorcycle=False):
        """Map fuel type values to model choices"""
        if pd.isna(fuel_type) or fuel_type is None:
            return None

        fuel = str(fuel_type).strip().upper()

        if is_motorcycle:
            mapping = {
                'GASOLINE': 'GASOLINE',
                'PETROL': 'GASOLINE',
                'ELECTRIC': 'ELECTRIC',
            }
        else:
            mapping = {
                'GASOLINE': 'GASOLINE',
                'PETROL': 'PETROL',
                'DIESEL': 'DIESEL',
                'ELECTRIC': 'ELECTRIC',
                'HYBRID': 'HYBRID',
                'PLUG-IN HYBRID': 'PLUG-IN HYBRID',
                'PLUG IN HYBRID': 'PLUG-IN HYBRID',
            }

        return mapping.get(fuel, fuel)

    @transaction.atomic
    def process_vehicles(self, df):
        """Process vehicle data from DataFrame"""
        created_vehicles = 0
        skipped_vehicles = 0

        for index, row in df.iterrows():
            try:
                # Extract and clean data
                make_name = self.clean_string(row.get('Make'))
                model_name = self.clean_string(row.get('Model'))
                model_number = self.clean_string(row.get('Model number'))
                transmission = self.map_transmission(row.get('Transmission'))
                drive_config = self.map_drive_configuration(row.get('Drive Configuration'))
                engine_capacity = self.clean_string(row.get('Engine Capacity'))
                body_type = self.map_body_type(row.get('Body Type '))  # Note the space in column name
                gvw = self.clean_string(row.get('GVW'))
                seating = self.clean_integer(row.get('Seating'))
                fuel_type = self.map_fuel_type(row.get('Fuel'))
                crsp = self.clean_decimal(row.get('CRSP (KES.)'))

                # Skip rows with missing essential data
                if not all([make_name, model_name, crsp]):
                    self.stdout.write(f"Skipping row {index + 2}: Missing essential data")
                    skipped_vehicles += 1
                    continue

                # Create or get VehicleMake
                vehicle_make, _ = VehicleMake.objects.get_or_create(name=make_name)

                # Create or get VehicleModel
                vehicle_model, _ = VehicleModel.objects.get_or_create(
                    make=vehicle_make,
                    name=model_name,
                    defaults={'model_number': model_number}
                )

                # Create Vehicle (with get_or_create to avoid duplicates)
                vehicle, created = Vehicle.objects.get_or_create(
                    make=vehicle_make,
                    model=vehicle_model,
                    model_number=model_number or '',
                    transmission=transmission or '',
                    drive_configuration=drive_config or '',
                    defaults={
                        'engine_capacity': engine_capacity or '',
                        'body_type': body_type or '',
                        'gvw': gvw,
                        'seating': seating,
                        'fuel_type': fuel_type or '',
                        'crsp': crsp,
                    }
                )

                if created:
                    created_vehicles += 1
                else:
                    # Update existing vehicle
                    vehicle.engine_capacity = engine_capacity or ''
                    vehicle.body_type = body_type or ''
                    vehicle.gvw = gvw
                    vehicle.seating = seating
                    vehicle.fuel_type = fuel_type or ''
                    vehicle.crsp = crsp
                    vehicle.save()

            except Exception as e:
                self.stdout.write(f"Error processing vehicle row {index + 2}: {str(e)}")
                skipped_vehicles += 1

        self.stdout.write(f"Vehicles: {created_vehicles} created/updated, {skipped_vehicles} skipped")

    @transaction.atomic
    def process_motorcycles(self, df):
        """Process motorcycle data from DataFrame"""
        created_motorcycles = 0
        skipped_motorcycles = 0

        for index, row in df.iterrows():
            try:
                # Extract and clean data
                make_name = self.clean_string(row.get('Make'))
                model_name = self.clean_string(row.get('Model'))
                model_number = self.clean_string(row.get('Model number'))
                transmission = self.map_transmission(row.get('Transmission'), is_motorcycle=True)
                engine_capacity = self.clean_string(row.get('Engine Capacity'))
                seating = self.clean_integer(row.get('seating'))
                fuel = self.map_fuel_type(row.get('Fuel'), is_motorcycle=True)
                crsp = self.clean_decimal(row.get('CRSP (KES)'))

                # Skip rows with missing essential data
                if not all([make_name, model_name, seating is not None, crsp]):
                    self.stdout.write(f"Skipping motorcycle row {index + 2}: Missing essential data")
                    skipped_motorcycles += 1
                    continue

                # Create or get MotorcycleMake
                motorcycle_make, _ = MotorcycleMake.objects.get_or_create(name=make_name)

                # Create or get MotorcycleModel
                motorcycle_model, _ = MotorcycleModel.objects.get_or_create(
                    make=motorcycle_make,
                    name=model_name,
                    defaults={'model_number': model_number}
                )

                # Create Motorcycle (with get_or_create to avoid duplicates)
                motorcycle, created = Motorcycle.objects.get_or_create(
                    make=motorcycle_make,
                    model=motorcycle_model,
                    model_number=model_number or '',
                    transmission=transmission,
                    engine_capacity=engine_capacity,
                    defaults={
                        'seating': seating,
                        'fuel': fuel or '',
                        'crsp': crsp,
                    }
                )

                if created:
                    created_motorcycles += 1
                else:
                    # Update existing motorcycle
                    motorcycle.seating = seating
                    motorcycle.fuel = fuel or ''
                    motorcycle.crsp = crsp
                    motorcycle.save()

            except Exception as e:
                self.stdout.write(f"Error processing motorcycle row {index + 2}: {str(e)}")
                skipped_motorcycles += 1

        self.stdout.write(f"Motorcycles: {created_motorcycles} created/updated, {skipped_motorcycles} skipped")
