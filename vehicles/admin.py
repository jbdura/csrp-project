from django.contrib import admin
from .models import VehicleMake, VehicleModel, Vehicle


@admin.register(VehicleMake)
class VehicleMakeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ("name", "make", "model_number")
    list_filter = ("make",)
    search_fields = ("name", "model_number")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        "make",
        "model",
        "model_number",
        "transmission",
        "drive_configuration",
        "engine_capacity",
        "body_type",
        "fuel_type",
        "seating",
        "crsp",
    )
    list_filter = (
        "make",
        "model",
        "transmission",
        "drive_configuration",
        "body_type",
        "fuel_type",
    )
    search_fields = ("make__name", "model__name", "model_number")
    ordering = ("make", "model")

# admin.py
from django.contrib import admin
from .models import (
    MotorcycleMake, MotorcycleModel, Motorcycle,
    HeavyMachineryMake, HeavyMachineryModel, HeavyMachinery
)


# ============== MOTORCYCLE ADMIN ==============

@admin.register(MotorcycleMake)
class MotorcycleMakeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(MotorcycleModel)
class MotorcycleModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'make', 'model_number']
    list_filter = ['make']
    search_fields = ['name', 'model_number', 'make__name']
    ordering = ['make', 'name']


@admin.register(Motorcycle)
class MotorcycleAdmin(admin.ModelAdmin):
    list_display = ['make', 'model', 'transmission', 'engine_capacity', 'fuel', 'seating', 'crsp']
    list_filter = ['make', 'fuel', 'transmission']
    search_fields = ['make__name', 'model__name', 'model_number']
    ordering = ['make', 'model']

    fieldsets = (
        ('Basic Information', {
            'fields': ('make', 'model', 'model_number')
        }),
        ('Specifications', {
            'fields': ('transmission', 'engine_capacity', 'seating', 'fuel')
        }),
        ('Pricing', {
            'fields': ('crsp',)
        }),
    )


# ============== HEAVY MACHINERY ADMIN ==============

@admin.register(HeavyMachineryMake)
class HeavyMachineryMakeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']
    ordering = ['name']


@admin.register(HeavyMachineryModel)
class HeavyMachineryModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'make']
    list_filter = ['make']
    search_fields = ['name', 'make__name']
    ordering = ['make', 'name']


@admin.register(HeavyMachinery)
class HeavyMachineryAdmin(admin.ModelAdmin):
    list_display = ['make', 'model', 'horsepower', 'crsp']
    list_filter = ['make']
    search_fields = ['make__name', 'model__name', 'horsepower']
    ordering = ['make', 'model']

    fieldsets = (
        ('Basic Information', {
            'fields': ('make', 'model')
        }),
        ('Specifications', {
            'fields': ('horsepower',)
        }),
        ('Pricing', {
            'fields': ('crsp',)
        }),
    )
