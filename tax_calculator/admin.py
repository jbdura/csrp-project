from django.contrib import admin
from .models import VehicleCategory, DepreciationRate, TaxCalculation, TaxConfiguration


@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category_type', 'import_duty_rate', 'excise_duty_rate',
        'excise_duty_fixed_amount', 'customs_factor', 'is_active'
    ]
    list_filter = ['is_active', 'category_type', 'exempt_import_duty', 'exempt_excise_duty']
    search_fields = ['name', 'description', 'category_type']
    list_editable = ['is_active']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category_type', 'description')
        }),
        ('Tax Rates', {
            'fields': (
                'customs_factor',
                'import_duty_rate',
                'excise_duty_rate',
                'excise_duty_fixed_amount',
            )
        }),
        ('Exemptions', {
            'fields': ('exempt_import_duty', 'exempt_excise_duty')
        }),
        ('HS Codes & Dates', {
            'fields': ('hs_codes', 'effective_from', 'effective_to', 'is_active')
        }),
    )


@admin.register(DepreciationRate)
class DepreciationRateAdmin(admin.ModelAdmin):
    list_display = [
        'import_type', 'vehicle_age_years', 'depreciation_rate',
        'effective_from', 'effective_to', 'is_active'
    ]
    list_filter = ['import_type', 'is_active']
    list_editable = ['depreciation_rate', 'is_active']
    ordering = ['import_type', 'vehicle_age_years']

    fieldsets = (
        ('Depreciation Details', {
            'fields': ('import_type', 'vehicle_age_years', 'depreciation_rate')
        }),
        ('Effective Dates', {
            'fields': ('effective_from', 'effective_to', 'is_active')
        }),
    )

    def get_queryset(self, request):
        """Group by import type for easier editing"""
        return super().get_queryset(request).order_by('import_type', 'vehicle_age_years')


@admin.register(TaxCalculation)
class TaxCalculationAdmin(admin.ModelAdmin):
    list_display = [
        'calculation_id', 'make', 'model', 'year_of_manufacture',
        'import_type', 'total_tax', 'total_cost', 'created_at'
    ]
    list_filter = ['vehicle_type', 'import_type', 'created_at', 'vehicle_category']
    search_fields = ['make', 'model', 'calculation_id']
    readonly_fields = [
        'calculation_id', 'created_at', 'ip_address',
        'vehicle_age', 'depreciation_rate', 'depreciated_value',
        'customs_value', 'import_duty', 'excise_value', 'excise_duty',
        'vat_value', 'vat', 'idf', 'rdl', 'total_tax', 'total_cost'
    ]
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Calculation ID', {
            'fields': ('calculation_id',)
        }),
        ('Vehicle Information', {
            'fields': (
                'vehicle_type', 'vehicle_id', 'make', 'model',
                'year_of_manufacture', 'engine_capacity', 'fuel_type'
            )
        }),
        ('Input Parameters', {
            'fields': (
                'import_type', 'vehicle_category', 'market_value_kes',
            )
        }),
        ('Depreciation', {
            'fields': ('vehicle_age', 'depreciation_rate', 'depreciated_value'),
            'classes': ('collapse',)
        }),
        ('Tax Calculations', {
            'fields': (
                'customs_value', 'import_duty', 'excise_value',
                'excise_duty', 'vat_value', 'vat', 'idf', 'rdl'
            ),
            'classes': ('collapse',)
        }),
        ('Totals', {
            'fields': ('total_tax', 'total_cost')
        }),
        ('Full Breakdown', {
            'fields': ('calculation_breakdown',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        """Prevent manual addition - calculations should come from API"""
        return False


@admin.register(TaxConfiguration)
class TaxConfigurationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'vat_rate', 'idf_rate', 'rdl_rate',
        'current_year', 'is_active', 'updated_at'
    ]
    list_editable = ['is_active']

    fieldsets = (
        ('Tax Rates', {
            'fields': ('vat_rate', 'idf_rate', 'rdl_rate'),
            'description': 'Core tax rates for calculations'
        }),
        ('System Settings', {
            'fields': ('current_year',),
            'description': 'Current year for age calculations'
        }),
        ('Estimated Additional Costs (KES)', {
            'fields': (
                'estimated_clearing_agent_fee',
                'estimated_port_handling',
                'estimated_ntsa_inspection',
                'estimated_registration',
                'estimated_transport',
            ),
            'description': 'Estimated costs shown to users for planning purposes'
        }),
        ('Metadata', {
            'fields': ('effective_from', 'is_active', 'notes', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['updated_at']

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of tax configuration"""
        return False
