# calculator/models.py
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from datetime import datetime

class DepreciationRate(models.Model):
    """Stores depreciation rates for different import types"""
    IMPORT_TYPE_CHOICES = [
        ('DIRECT', 'Direct Import'),
        ('PREVIOUSLY_REGISTERED', 'Previously Registered in Kenya'),
    ]

    import_type = models.CharField(max_length=30, choices=IMPORT_TYPE_CHOICES)
    years_from = models.IntegerField(validators=[MinValueValidator(0)])
    years_to = models.IntegerField(validators=[MinValueValidator(0)])
    depreciation_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        unique_together = ['import_type', 'years_from', 'years_to']
        ordering = ['import_type', 'years_from']

    def __str__(self):
        return f"{self.import_type}: {self.years_from}-{self.years_to} years = {self.depreciation_percentage}%"


class VehicleCategory(models.Model):
    """Defines vehicle categories and their tax rates"""
    CATEGORY_CHOICES = [
        ('VEHICLE_1500CC_BELOW', 'Vehicles ≤1500cc'),
        ('VEHICLE_ABOVE_1500CC', 'Vehicles >1500cc (Standard)'),
        ('VEHICLE_LUXURY', 'Luxury Vehicles (>3000cc petrol / >2500cc diesel)'),
        ('VEHICLE_ELECTRIC', '100% Electric Vehicles'),
        ('SCHOOL_BUS', 'School Buses for Public Schools'),
        ('PRIME_MOVER', 'Prime Movers'),
        ('TRAILER', 'Trailers'),
        ('AMBULANCE', 'Ambulances'),
        ('MOTORCYCLE', 'Motorcycles'),
        ('SPECIAL_PURPOSE', 'Special Purpose Vehicles'),
        ('HEAVY_MACHINERY', 'Heavy Machinery'),
    ]

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, unique=True)
    import_duty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    excise_duty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    excise_duty_fixed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed excise duty amount (for motorcycles)"
    )
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    customs_value_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of depreciated CRSP to calculate customs value"
    )

    def __str__(self):
        return self.get_category_display()


class TaxCalculation(models.Model):
    """Stores calculation history for reference"""
    IMPORT_TYPE_CHOICES = [
        ('DIRECT', 'Direct Import'),
        ('PREVIOUSLY_REGISTERED', 'Previously Registered in Kenya'),
    ]

    VEHICLE_TYPE_CHOICES = [
        ('VEHICLE', 'Vehicle'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('HEAVY_MACHINERY', 'Heavy Machinery'),
    ]

    # Reference to the vehicle
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    vehicle_id = models.IntegerField()  # Generic foreign key reference

    # Input parameters
    import_type = models.CharField(max_length=30, choices=IMPORT_TYPE_CHOICES)
    year_of_manufacture = models.IntegerField(validators=[MinValueValidator(1900)])
    current_year = models.IntegerField()

    # CRSP and depreciation
    original_crsp = models.DecimalField(max_digits=15, decimal_places=2)
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2)
    depreciated_value = models.DecimalField(max_digits=15, decimal_places=2)

    # Tax components
    customs_value = models.DecimalField(max_digits=15, decimal_places=2)
    import_duty = models.DecimalField(max_digits=15, decimal_places=2)
    excise_value = models.DecimalField(max_digits=15, decimal_places=2)
    excise_duty = models.DecimalField(max_digits=15, decimal_places=2)
    vat_value = models.DecimalField(max_digits=15, decimal_places=2)
    vat = models.DecimalField(max_digits=15, decimal_places=2)
    rdl = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    idf = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Total
    total_taxes = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    calculation_reference = models.UUIDField(unique=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vehicle_type} - {self.calculation_reference}"
