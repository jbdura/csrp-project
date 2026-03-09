from rest_framework import serializers
from .models import TaxCalculation, VehicleCategory, DepreciationRate, TaxConfiguration


class TaxCalculationInputSerializer(serializers.Serializer):
    """Input validation for tax calculation"""
    vehicle_type = serializers.ChoiceField(
        choices=['VEHICLE', 'MOTORCYCLE', 'HEAVY_MACHINERY'],
        help_text="Type of vehicle"
    )
    vehicle_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="ID from vehicles app (optional)"
    )

    # CRSP - Government's official retail price (for tax calculation)
    market_value_kes = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0,
        help_text="Government CRSP in KES (for tax calculation)"
    )

    # NEW: Actual purchase cost
    purchase_cost_kes = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=0,
        required=False,
        allow_null=True,
        help_text="Actual purchase cost (CIF) in KES"
    )

    year_of_manufacture = serializers.IntegerField(
        min_value=1990,
        max_value=2025,
        help_text="Year the vehicle was manufactured"
    )
    import_type = serializers.ChoiceField(
        choices=['DIRECT', 'PREVIOUSLY_REGISTERED'],
        help_text="Import type"
    )
    engine_capacity = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="Engine capacity in cc (optional, auto-detected if vehicle_id provided)"
    )
    fuel_type = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Fuel type (optional, auto-detected if vehicle_id provided)"
    )
    category_type = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True,
        help_text="Explicit category type (optional, auto-detected if not provided)"
    )

class TaxCalculationSerializer(serializers.ModelSerializer):
    """Output serializer for saved calculations"""
    category_name = serializers.CharField(source='vehicle_category.name', read_only=True)
    category_type = serializers.CharField(source='vehicle_category.category_type', read_only=True)
    formatted_total_tax = serializers.CharField(read_only=True)
    formatted_total_cost = serializers.CharField(read_only=True)
    import_type_display = serializers.CharField(source='get_import_type_display', read_only=True)
    vehicle_type_display = serializers.CharField(source='get_vehicle_type_display', read_only=True)

    class Meta:
        model = TaxCalculation
        fields = [
            'id', 'calculation_id', 'vehicle_type', 'vehicle_type_display',
            'vehicle_id', 'make', 'model', 'fuel_type', 'engine_capacity',
            'year_of_manufacture', 'vehicle_age', 'import_type', 'import_type_display',
            'category_name', 'category_type', 'market_value_kes',
            'depreciation_rate', 'depreciated_value', 'customs_value',
            'import_duty', 'excise_value', 'excise_duty', 'vat_value', 'vat',
            'idf', 'rdl', 'total_tax', 'total_cost',
            'formatted_total_tax', 'formatted_total_cost',
            'calculation_breakdown', 'created_at', 'ip_address'
        ]
        read_only_fields = ['calculation_id', 'created_at']


class TaxCalculationListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing calculations"""
    category_name = serializers.CharField(source='vehicle_category.name', read_only=True)
    formatted_total_tax = serializers.CharField(read_only=True)
    formatted_total_cost = serializers.CharField(read_only=True)

    class Meta:
        model = TaxCalculation
        fields = [
            'id', 'calculation_id', 'make', 'model', 'year_of_manufacture',
            'import_type', 'category_name', 'total_tax', 'total_cost',
            'formatted_total_tax', 'formatted_total_cost', 'created_at'
        ]


class VehicleCategorySerializer(serializers.ModelSerializer):
    """Serializer for vehicle categories"""
    excise_display = serializers.SerializerMethodField()

    class Meta:
        model = VehicleCategory
        fields = [
            'id', 'name', 'category_type', 'description',
            'customs_factor', 'import_duty_rate', 'excise_duty_rate',
            'excise_duty_fixed_amount', 'excise_display',
            'exempt_import_duty', 'exempt_excise_duty',
            'hs_codes', 'is_active'
        ]

    def get_excise_display(self, obj):
        """Display excise duty in readable format"""
        if obj.exempt_excise_duty:
            return "Exempt"
        elif obj.excise_duty_fixed_amount:
            return f"KES {obj.excise_duty_fixed_amount:,.2f} (Fixed)"
        elif obj.excise_duty_rate:
            return f"{obj.excise_duty_rate}%"
        return "N/A"


class DepreciationRateSerializer(serializers.ModelSerializer):
    """Serializer for depreciation rates"""
    import_type_display = serializers.CharField(source='get_import_type_display', read_only=True)

    class Meta:
        model = DepreciationRate
        fields = [
            'id', 'import_type', 'import_type_display',
            'vehicle_age_years', 'depreciation_rate', 'is_active'
        ]


class TaxConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for tax configuration"""
    total_estimated_additional_costs = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = TaxConfiguration
        fields = [
            'id', 'vat_rate', 'idf_rate', 'rdl_rate', 'current_year',
            'estimated_clearing_agent_fee', 'estimated_port_handling',
            'estimated_ntsa_inspection', 'estimated_registration',
            'estimated_transport', 'total_estimated_additional_costs',
            'effective_from', 'is_active', 'notes', 'updated_at'
        ]


class ComparisonInputSerializer(serializers.Serializer):
    """Input for comparing import types"""
    vehicle_type = serializers.ChoiceField(choices=['VEHICLE', 'MOTORCYCLE', 'HEAVY_MACHINERY'])
    vehicle_id = serializers.IntegerField(required=False, allow_null=True)
    market_value_kes = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0)
    year_of_manufacture = serializers.IntegerField(min_value=1990, max_value=2025)
    engine_capacity = serializers.IntegerField(required=False, allow_null=True)
    fuel_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    category_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
