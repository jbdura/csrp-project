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
