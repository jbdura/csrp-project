from django.contrib import admin
from .models import VehicleMake, VehicleModel, Vehicle

@admin.register(VehicleMake)
class VehicleMakeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ['make', 'name', 'model_number']
    list_filter = ['make']
    search_fields = ['name', 'model_number']

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['make', 'model', 'transmission', 'fuel_type', 'crsp']
    list_filter = ['make', 'fuel_type', 'transmission', 'body_type']
    search_fields = ['make__name', 'model__name', 'model_number']
