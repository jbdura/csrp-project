# calculator/admin.py
from django.contrib import admin
from .models import DepreciationRate, VehicleCategory, TaxCalculation

@admin.register(DepreciationRate)
class DepreciationRateAdmin(admin.ModelAdmin):
    list_display = ['import_type', 'years_from', 'years_to', 'depreciation_percentage']
    list_filter = ['import_type']
    ordering = ['import_type', 'years_from']

@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = ['category', 'import_duty_rate', 'excise_duty_rate', 'vat_rate', 'customs_value_percentage']
    list_filter = ['category']

@admin.register(TaxCalculation)
class TaxCalculationAdmin(admin.ModelAdmin):
    list_display = ['calculation_reference', 'vehicle_type', 'import_type', 'total_taxes', 'created_at']
    list_filter = ['vehicle_type', 'import_type', 'created_at']
    readonly_fields = ['calculation_reference', 'created_at']
    date_hierarchy = 'created_at'
