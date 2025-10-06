from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid

class VehicleMake(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class VehicleModel(models.Model):
    make = models.ForeignKey(VehicleMake, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    model_number = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['make', 'name']

    def __str__(self):
        return f"{self.make.name} {self.name}"

class Vehicle(models.Model):
    TRANSMISSION_CHOICES = [
        ('AT', 'Automatic'),
        ('MT', 'Manual'),
        ('CVT', 'CVT'),
        ('AMT', 'Automated Manual'),
    ]

    DRIVE_CONFIG_CHOICES = [
        ('FWD', 'Front Wheel Drive'),
        ('RWD', 'Rear Wheel Drive'),
        ('4WD', 'Four Wheel Drive'),
        ('AWD', 'All Wheel Drive'),
        ('2WD', 'Two Wheel Drive'),
    ]

    BODY_TYPE_CHOICES = [
        ('SUV', 'SUV'),
        ('SEDAN', 'Sedan'),
        ('HATCHBACK', 'Hatchback'),
        ('WAGON', 'Wagon'),
        ('S.WAGON', 'Station Wagon'),
        ('COUPE', 'Coupe'),
        ('CONVERTIBLE', 'Convertible'),
        ('VAN', 'Van'),
        ('TRUCK', 'Truck'),
        ('PICKUP', 'Pickup'),
    ]

    FUEL_TYPE_CHOICES = [
        ('GASOLINE', 'Gasoline'),
        ('DIESEL', 'Diesel'),
        ('ELECTRIC', 'Electric'),
        ('HYBRID', 'Hybrid'),
        ('PLUG-IN HYBRID', 'Plug-in Hybrid'),
        ('PETROL', 'Petrol'),
    ]

    make = models.ForeignKey(VehicleMake, on_delete=models.CASCADE)
    model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE)
    model_number = models.CharField(max_length=100, blank=True, null=True)
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_CHOICES)
    drive_configuration = models.CharField(max_length=10, choices=DRIVE_CONFIG_CHOICES)
    engine_capacity = models.CharField(max_length=50)  # Can be cc or kWh for electric
    body_type = models.CharField(max_length=20, choices=BODY_TYPE_CHOICES)
    gvw = models.CharField(max_length=50, blank=True, null=True)  # Gross Vehicle Weight
    seating = models.IntegerField(blank=True, null=True)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES)

    # Updated CRSP field with better constraints for money
    crsp = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Cost (KES)',
        help_text='Cost in Kenyan Shillings'
    )

    class Meta:
        unique_together = ['make', 'model', 'model_number', 'transmission', 'drive_configuration']

    def __str__(self):
        return f"{self.make.name} {self.model.name} - {self.fuel_type}"

    @property
    def crsp_in_cents(self):
        """Returns the cost in cents (100 cents = 1 KES)"""
        return int(self.crsp * 100)

    @property
    def formatted_price(self):
        """Returns formatted price string"""
        return f"KES {self.crsp:,.2f}"


# ============== MOTORCYCLE MODELS ==============

class MotorcycleMake(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class MotorcycleModel(models.Model):
    make = models.ForeignKey(MotorcycleMake, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    model_number = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['make', 'name']

    def __str__(self):
        return f"{self.make.name} {self.name}"


class Motorcycle(models.Model):

    MOTORCYCLE_TRANSMISSION_CHOICES = [
        ("3MT", "3-speed Manual"),
        ("4MT", "4-speed Manual"),
        ("5MT", "5-speed Manual"),
        ("6MT", "6-speed Manual"),
        ("CVT", "Continuously Variable Transmission"),
        ("DCT", "Dual Clutch Transmission"),
        ("AUTO", "Automatic (Other)"),
        ("NONE", "No Gears / Electric"),
    ]

    MOTORCYCLE_FUEL_CHOICES = [
        ("GASOLINE", "Gasoline"),
        ("ELECTRIC", "Electric"),
    ]

    make = models.ForeignKey(MotorcycleMake, on_delete=models.CASCADE)
    model = models.ForeignKey(MotorcycleModel, on_delete=models.CASCADE)
    model_number = models.CharField(max_length=100, blank=True, null=True)
    transmission = models.CharField(
        max_length=10,
        choices=MOTORCYCLE_TRANSMISSION_CHOICES,
        blank=True,
        null=True
    )
    engine_capacity = models.CharField(max_length=50, blank=True, null=True)  # Can be cc or null
    seating = models.IntegerField()
    fuel = models.CharField(max_length=20, choices=MOTORCYCLE_FUEL_CHOICES)

    # Updated CRSP field with better constraints for money
    crsp = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Cost (KES)',
        help_text='Cost in Kenyan Shillings'
    )

    class Meta:
        unique_together = ['make', 'model', 'model_number', 'transmission', 'engine_capacity']

    def __str__(self):
        return f"{self.make.name} {self.model.name} - {self.fuel}"

    @property
    def crsp_in_cents(self):
        """Returns the cost in cents (100 cents = 1 KES)"""
        return int(self.crsp * 100)

    @property
    def formatted_price(self):
        """Returns formatted price string"""
        return f"KES {self.crsp:,.2f}"


# ============== HEAVY MACHINERY MODELS ==============

"""
This entails tractors and graders
"""
class HeavyMachineryMake(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class HeavyMachineryModel(models.Model):
    make = models.ForeignKey(HeavyMachineryMake, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)

    class Meta:
        unique_together = ['make', 'name']

    def __str__(self):
        return f"{self.make.name} {self.name}"


class HeavyMachinery(models.Model):
    make = models.ForeignKey(HeavyMachineryMake, on_delete=models.CASCADE)
    model = models.ForeignKey(HeavyMachineryModel, on_delete=models.CASCADE)
    horsepower = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Horsepower (leave empty if no engine)'
    )  # Now optional for machinery without engines

    crsp = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Cost (KES)',
        help_text='Cost in Kenyan Shillings'
    )

    class Meta:
        unique_together = ['make', 'model', 'horsepower']

    def __str__(self):
        if self.horsepower:
            return f"{self.make.name} {self.model.name} - {self.horsepower} HP"
        return f"{self.make.name} {self.model.name}"

    @property
    def crsp_in_cents(self):
        """Returns the cost in cents (100 cents = 1 KES)"""
        return int(self.crsp * 100)

    @property
    def formatted_price(self):
        """Returns formatted price string"""
        return f"KES {self.crsp:,.2f}"