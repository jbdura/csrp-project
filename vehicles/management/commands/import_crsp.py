# management/commands/import_crsp_data.py
import pandas as pd
import logging
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.exceptions import ValidationError
import os
import sys

# Import your models (adjust the import path as needed)
from vehicles.models import (
    VehicleMake, VehicleModel, Vehicle,
    MotorcycleMake, MotorcycleModel, Motorcycle
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Import CRSP data from Excel file for vehicles and motorcycles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='CRSP.xlsx',
            help='Path to the Excel file (default: CRSP.xlsx)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run the import without saving to database'
        )
        parser.add_argument(
            '--skip-errors',
            action='store_true',
            help='Continue import even if some rows fail'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        skip_errors = options['skip_errors']

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS(f'Starting import from {file_path}'))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be saved'))

        try:
            # Process vehicles
            self.import_vehicles(file_path, dry_run, skip_errors)

            # Process motorcycles
            self.import_motorcycles(file_path, dry_run, skip_errors)

            self.stdout.write(self.style.SUCCESS('Import completed successfully!'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Import failed: {str(e)}'))
            logger.exception("Import failed with exception")
            sys.exit(1)

    def clean_string(self, value):
        """Clean and normalize string values"""
        if pd.isna(value) or value == '' or str(value).strip().upper() in ['N/A', 'NA', 'NULL', 'NONE', '-']:
            return None
        return str(value).strip()

    def clean_decimal(self, value):
        """Clean and convert decimal values"""
        if pd.isna(value) or value == '':
            return Decimal('0.00')

        # Remove any non-numeric characters except decimal point
        cleaned = str(value).replace(',', '').replace('KES', '').replace('KSH', '').strip()

        try:
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            logger.warning(f"Could not convert '{value}' to decimal, using 0.00")
            return Decimal('0.00')

    def clean_integer(self, value, default=None):
        """Clean and convert integer values"""
        if pd.isna(value) or value == '':
            return default

        try:
            # Handle ranges like "5-7" by taking the first number
            cleaned = str(value).split('-')[0].strip()
            return int(float(cleaned))
        except (ValueError, TypeError):
            logger.warning(f"Could not convert '{value}' to integer, using default {default}")
            return default

    def map_transmission(self, transmission, is_motorcycle=False):
        """Map transmission values to model choices"""
        if not transmission:
            return None if is_motorcycle else 'MT'  # Default for vehicles

        trans_upper = transmission.upper()

        if is_motorcycle:
            # Motorcycle transmission mapping
            if 'CVT' in trans_upper:
                return 'CVT'
            elif 'DCT' in trans_upper:
                return 'DCT'
            elif 'AUTO' in trans_upper:
                return 'AUTO'
            elif 'ELECTRIC' in trans_upper or 'NONE' in trans_upper:
                return 'NONE'
            elif '3' in trans_upper:
                return '3MT'
            elif '4' in trans_upper:
                return '4MT'
            elif '5' in trans_upper:
                return '5MT'
            elif '6' in trans_upper:
                return '6MT'
            else:
                return '5MT'  # Default
        else:
            # Vehicle transmission mapping
            if 'AUTO' in trans_upper or 'AT' in trans_upper:
                return 'AT'
            elif 'CVT' in trans_upper:
                return 'CVT'
            elif 'AMT' in trans_upper:
                return 'AMT'
            elif 'MANUAL' in trans_upper or 'MT' in trans_upper:
                return 'MT'
            else:
                return 'MT'  # Default

    def map_drive_config(self, drive_config):
        """Map drive configuration values to model choices"""
        if not drive_config:
            return 'FWD'  # Default

        config_upper = drive_config.upper()

        if 'AWD' in config_upper or 'ALL' in config_upper:
            return 'AWD'
        elif '4WD' in config_upper or 'FOUR' in config_upper:
            return '4WD'
        elif 'RWD' in config_upper or 'REAR' in config_upper:
            return 'RWD'
        elif '2WD' in config_upper or 'TWO' in config_upper:
            return '2WD'
        else:
            return 'FWD'  # Default

    def map_body_type(self, body_type):
        """Map body type values to model choices"""
        if not body_type:
            return 'SEDAN'  # Default

        body_upper = body_type.upper()

        if 'SUV' in body_upper:
            return 'SUV'
        elif 'SEDAN' in body_upper:
            return 'SEDAN'
        elif 'HATCH' in body_upper:
            return 'HATCHBACK'
        elif 'WAGON' in body_upper and 'STATION' in body_upper:
            return 'S.WAGON'
        elif 'WAGON' in body_upper:
            return 'WAGON'
        elif 'COUPE' in body_upper:
            return 'COUPE'
        elif 'CONVERT' in body_upper:
            return 'CONVERTIBLE'
        elif 'VAN' in body_upper:
            return 'VAN'
        elif 'TRUCK' in body_upper:
            return 'TRUCK'
        elif 'PICKUP' in body_upper or 'PICK UP' in body_upper:
            return 'PICKUP'
        else:
            return 'SEDAN'  # Default

    def map_fuel_type(self, fuel_type, is_motorcycle=False):
        """Map fuel type values to model choices"""
        if not fuel_type:
            return 'GASOLINE'  # Default

        fuel_upper = fuel_type.upper()

        if is_motorcycle:
            if 'ELECTRIC' in fuel_upper:
                return 'ELECTRIC'
            else:
                return 'GASOLINE'
        else:
            if 'DIESEL' in fuel_upper:
                return 'DIESEL'
            elif 'ELECTRIC' in fuel_upper and 'HYBRID' not in fuel_upper:
                return 'ELECTRIC'
            elif 'PLUG' in fuel_upper:
                return 'PLUG-IN HYBRID'
            elif 'HYBRID' in fuel_upper:
                return 'HYBRID'
            elif 'PETROL' in fuel_upper:
                return 'PETROL'
            else:
                return 'GASOLINE'

    @transaction.atomic
    def import_vehicles(self, file_path, dry_run, skip_errors):
        """Import vehicle data from Excel"""
        self.stdout.write('Importing vehicles...')

        try:
            # Read the vehicles sheet
            df = pd.read_excel(file_path, sheet_name='M.Vehicle CRSP July 2025')

            # Clean column names
            df.columns = df.columns.str.strip()

            success_count = 0
            error_count = 0

            for index, row in df.iterrows():
                try:
                    # Extract and clean data
                    make_name = self.clean_string(row.get('Make'))
                    model_name = self.clean_string(row.get('Model'))

                    if not make_name or not model_name:
                        logger.warning(f"Row {index + 2}: Missing make or model, skipping")
                        continue

                    model_number = self.clean_string(row.get('Model number', row.get('Model\nnumber')))
                    transmission = self.map_transmission(
                        self.clean_string(row.get('Transmission'))
                    )
                    drive_config = self.map_drive_config(
                        self.clean_string(row.get('Drive Configuration', row.get('Drive\nConfiguration')))
                    )
                    engine_capacity = self.clean_string(
                        row.get('Engine Capacity', row.get('Engine\nCapacity'))
                    ) or 'N/A'
                    body_type = self.map_body_type(
                        self.clean_string(row.get('Body Type', row.get('Body\nType')))
                    )
                    gvw = self.clean_string(row.get('GVW'))
                    seating = self.clean_integer(row.get('Seating'))
                    fuel_type = self.map_fuel_type(
                        self.clean_string(row.get('Fuel'))
                    )
                    crsp = self.clean_decimal(row.get('CRSP (KES.)', row.get('CRSP (KES)')))

                    if not dry_run:
                        # Create or get VehicleMake
                        vehicle_make, _ = VehicleMake.objects.get_or_create(
                            name=make_name
                        )

                        # Create or get VehicleModel
                        vehicle_model, _ = VehicleModel.objects.get_or_create(
                            make=vehicle_make,
                            name=model_name,
                            defaults={'model_number': model_number}
                        )

                        # Create or update Vehicle
                        vehicle, created = Vehicle.objects.update_or_create(
                            make=vehicle_make,
                            model=vehicle_model,
                            model_number=model_number,
                            transmission=transmission,
                            drive_configuration=drive_config,
                            defaults={
                                'engine_capacity': engine_capacity,
                                'body_type': body_type,
                                'gvw': gvw,
                                'seating': seating,
                                'fuel_type': fuel_type,
                                'crsp': crsp
                            }
                        )

                        action = "Created" if created else "Updated"
                        logger.info(f"{action} vehicle: {vehicle}")

                    success_count += 1

                except ValidationError as e:
                    error_count += 1
                    error_msg = f"Row {index + 2}: Validation error - {str(e)}"
                    logger.error(error_msg)
                    if not skip_errors:
                        raise

                except Exception as e:
                    error_count += 1
                    error_msg = f"Row {index + 2}: Unexpected error - {str(e)}"
                    logger.error(error_msg)
                    if not skip_errors:
                        raise

            self.stdout.write(
                self.style.SUCCESS(
                    f'Vehicles: {success_count} imported successfully, {error_count} errors'
                )
            )

        except Exception as e:
            logger.error(f"Failed to import vehicles: {str(e)}")
            raise

    @transaction.atomic
    def import_motorcycles(self, file_path, dry_run, skip_errors):
        """Import motorcycle data from Excel"""
        self.stdout.write('Importing motorcycles...')

        try:
            # Read the motorcycles sheet
            df = pd.read_excel(file_path, sheet_name='Motor Cycles July 2025')

            # Clean column names
            df.columns = df.columns.str.strip()

            success_count = 0
            error_count = 0

            for index, row in df.iterrows():
                try:
                    # Extract and clean data
                    make_name = self.clean_string(row.get('Make'))
                    model_name = self.clean_string(row.get('Model'))

                    if not make_name or not model_name:
                        logger.warning(f"Row {index + 2}: Missing make or model, skipping")
                        continue

                    model_number = self.clean_string(row.get('Model number'))
                    transmission = self.map_transmission(
                        self.clean_string(row.get('Transmission')),
                        is_motorcycle=True
                    )
                    engine_capacity = self.clean_string(row.get('Engine Capacity'))
                    seating = self.clean_integer(row.get('seating'), default=2)
                    fuel = self.map_fuel_type(
                        self.clean_string(row.get('Fuel')),
                        is_motorcycle=True
                    )
                    crsp = self.clean_decimal(row.get('CRSP (KES)', row.get('CRSP (KES.)')))

                    if not dry_run:
                        # Create or get MotorcycleMake
                        motorcycle_make, _ = MotorcycleMake.objects.get_or_create(
                            name=make_name
                        )

                        # Create or get MotorcycleModel
                        motorcycle_model, _ = MotorcycleModel.objects.get_or_create(
                            make=motorcycle_make,
                            name=model_name,
                            defaults={'model_number': model_number}
                        )

                        # Create or update Motorcycle
                        motorcycle, created = Motorcycle.objects.update_or_create(
                            make=motorcycle_make,
                            model=motorcycle_model,
                            model_number=model_number,
                            transmission=transmission,
                            engine_capacity=engine_capacity,
                            defaults={
                                'seating': seating or 2,
                                'fuel': fuel,
                                'crsp': crsp
                            }
                        )

                        action = "Created" if created else "Updated"
                        logger.info(f"{action} motorcycle: {motorcycle}")

                    success_count += 1

                except ValidationError as e:
                    error_count += 1
                    error_msg = f"Row {index + 2}: Validation error - {str(e)}"
                    logger.error(error_msg)
                    if not skip_errors:
                        raise

                except Exception as e:
                    error_count += 1
                    error_msg = f"Row {index + 2}: Unexpected error - {str(e)}"
                    logger.error(error_msg)
                    if not skip_errors:
                        raise

            self.stdout.write(
                self.style.SUCCESS(
                    f'Motorcycles: {success_count} imported successfully, {error_count} errors'
                )
            )

        except Exception as e:
            logger.error(f"Failed to import motorcycles: {str(e)}")
            raise
