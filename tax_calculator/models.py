from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class VehicleCategory(models.Model):
    """
    Defines different vehicle categories with their tax rates
    Examples: Passenger Car ≤1500cc, Electric Vehicle, Ambulance, etc.
    """
    CATEGORY_TYPES = [
        ('PASSENGER_CAR_SMALL', 'Passenger Car ≤1500cc'),
        ('PASSENGER_CAR_MEDIUM', 'Passenger Car >1500cc'),
        ('PASSENGER_CAR_LARGE', 'Passenger Car >3000cc petrol / >2500cc diesel'),
        ('ELECTRIC_VEHICLE', '100% Electric Vehicle'),
        ('HYBRID_VEHICLE', 'Hybrid Vehicle'),
        ('BUS', 'Bus'),
        ('SCHOOL_BUS', 'School Bus (Public Schools)'),
        ('TRUCK', 'Truck/Lorry'),
        ('PRIME_MOVER', 'Prime Mover'),
        ('TRAILER', 'Trailer'),
        ('AMBULANCE', 'Ambulance'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('SPECIAL_PURPOSE', 'Special Purpose Vehicle'),
        ('HEAVY_MACHINERY', 'Heavy Machinery'),
    ]

    name = models.CharField(max_length=100, unique=True)
    category_type = models.CharField(max_length=50, choices=CATEGORY_TYPES, unique=True)
    description = models.TextField(blank=True)

    # Tax rates
    customs_factor = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        help_text="Factor to convert retail price to customs value (e.g., 0.426 for 42.6%)"
    )
    import_duty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Import duty percentage (e.g., 35.00 for 35%)"
    )
    excise_duty_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Excise duty percentage (e.g., 20.00 for 20%)",
        null=True,
        blank=True
    )
    excise_duty_fixed_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Fixed excise amount for motorcycles (KES)"
    )

    # Special flags
    exempt_import_duty = models.BooleanField(default=False)
    exempt_excise_duty = models.BooleanField(default=False)

    # HS Codes (optional)
    hs_codes = models.TextField(
        blank=True,
        help_text="Comma-separated HS codes (e.g., 8703.24.90, 8703.33.90)"
    )

    # Metadata
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Vehicle Categories"
        ordering = ['name']

    def __str__(self):
        excise_display = f"{self.excise_duty_rate}%" if self.excise_duty_rate else "Fixed"
        return f"{self.name} (Import: {self.import_duty_rate}% / Excise: {excise_display})"


class DepreciationRate(models.Model):
    """
    Age-based depreciation rates for vehicles
    These rates change yearly and must be editable
    """
    IMPORT_TYPE_CHOICES = [
        ('DIRECT', 'Direct Import'),
        ('PREVIOUSLY_REGISTERED', 'Previously Registered in Kenya'),
    ]

    import_type = models.CharField(max_length=25, choices=IMPORT_TYPE_CHOICES)
    vehicle_age_years = models.IntegerField(
        help_text="Age of vehicle in years (e.g., 1, 2, 3...)"
    )
    depreciation_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Depreciation percentage (e.g., 20.00 for 20%)"
    )

    # Effective dates
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['import_type', 'vehicle_age_years', 'effective_from']
        ordering = ['import_type', 'vehicle_age_years']

    def __str__(self):
        return f"{self.get_import_type_display()} - {self.vehicle_age_years} years: {self.depreciation_rate}%"


class TaxCalculation(models.Model):
    """
    Stores tax calculation results
    Saved only when user explicitly requests
    """
    VEHICLE_TYPE_CHOICES = [
        ('VEHICLE', 'Car/Truck/Bus'),
        ('MOTORCYCLE', 'Motorcycle'),
        ('HEAVY_MACHINERY', 'Heavy Machinery'),
    ]

    IMPORT_TYPE_CHOICES = [
        ('DIRECT', 'Direct Import'),
        ('PREVIOUSLY_REGISTERED', 'Previously Registered'),
    ]

    # Unique identifier
    calculation_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Input data
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPE_CHOICES)
    vehicle_id = models.IntegerField(null=True, blank=True, help_text="ID from vehicles app")

    market_value_kes = models.DecimalField(max_digits=15, decimal_places=2)
    year_of_manufacture = models.IntegerField()
    engine_capacity = models.IntegerField(null=True, blank=True, help_text="Engine in cc")
    import_type = models.CharField(max_length=25, choices=IMPORT_TYPE_CHOICES)

    vehicle_category = models.ForeignKey(
        VehicleCategory,
        on_delete=models.PROTECT,
        related_name='calculations'
    )

    # Vehicle details (denormalized for history)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=200, blank=True)
    fuel_type = models.CharField(max_length=50, blank=True)

    # Calculated values
    vehicle_age = models.IntegerField()
    depreciation_rate = models.DecimalField(max_digits=5, decimal_places=2)
    depreciated_value = models.DecimalField(max_digits=15, decimal_places=2)
    customs_value = models.DecimalField(max_digits=15, decimal_places=2)

    # Taxes
    import_duty = models.DecimalField(max_digits=15, decimal_places=2)
    excise_value = models.DecimalField(max_digits=15, decimal_places=2)
    excise_duty = models.DecimalField(max_digits=15, decimal_places=2)
    vat_value = models.DecimalField(max_digits=15, decimal_places=2)
    vat = models.DecimalField(max_digits=15, decimal_places=2)
    idf = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    rdl = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    # Totals
    total_tax = models.DecimalField(max_digits=15, decimal_places=2)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2)

    # Full breakdown as JSON (for future reference)
    calculation_breakdown = models.JSONField(default=dict)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['calculation_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['vehicle_type']),
        ]

    def __str__(self):
        vehicle_name = f"{self.make} {self.model}" if self.make else f"{self.vehicle_type}"
        return f"{vehicle_name} - {self.calculation_id}"

    @property
    def formatted_total_tax(self):
        """Returns formatted total tax"""
        return f"KES {self.total_tax:,.2f}"

    @property
    def formatted_total_cost(self):
        """Returns formatted total cost"""
        return f"KES {self.total_cost:,.2f}"


class TaxConfiguration(models.Model):
    """
    System-wide tax configuration
    Single instance, updated when rates change
    """
    # VAT
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=16.00,
        help_text="VAT percentage (default 16%)"
    )

    # Fees for direct imports
    idf_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=3.500,
        help_text="Import Declaration Fee percentage (default 3.5%)"
    )
    rdl_rate = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=2.000,
        help_text="Road Development Levy percentage (default 2%)"
    )

    # Additional estimated costs (for user reference)
    estimated_clearing_agent_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        help_text="Estimated clearing agent fee in KES"
    )
    estimated_port_handling = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15000,
        help_text="Estimated port handling charges in KES"
    )
    estimated_ntsa_inspection = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5000,
        help_text="Estimated NTSA inspection fee in KES"
    )
    estimated_registration = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=20000,
        help_text="Estimated registration and number plates in KES"
    )
    estimated_transport = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=25000,
        help_text="Estimated transport from Mombasa in KES"
    )

    # Current year for age calculation
    current_year = models.IntegerField(default=2025)

    # Metadata
    effective_from = models.DateField()
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tax Configuration"
        verbose_name_plural = "Tax Configuration"

    def __str__(self):
        return f"Tax Config (VAT: {self.vat_rate}%, IDF: {self.idf_rate}%, RDL: {self.rdl_rate}%)"

    @classmethod
    def get_active_config(cls):
        """Get current active configuration"""
        return cls.objects.filter(is_active=True).first()

    @property
    def total_estimated_additional_costs(self):
        """Calculate total estimated additional costs"""
        return (
                self.estimated_clearing_agent_fee +
                self.estimated_port_handling +
                self.estimated_ntsa_inspection +
                self.estimated_registration +
                self.estimated_transport
        )
