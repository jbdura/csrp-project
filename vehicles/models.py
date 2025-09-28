from django.db import models

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
    crsp = models.DecimalField(max_digits=15, decimal_places=2)  # Cost in KES

    class Meta:
        unique_together = ['make', 'model', 'model_number', 'transmission', 'drive_configuration']

    def __str__(self):
        return f"{self.make.name} {self.model.name} - {self.fuel_type}"


