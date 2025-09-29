# calculator/serializers.py
from rest_framework import serializers
from vehicles.models import Vehicle, Motorcycle, HeavyMachinery
from .models import TaxCalculation, VehicleCategory, DepreciationRate
from decimal import Decimal
from datetime import datetime
import uuid

class VehicleSelectionSerializer(serializers.Serializer):
    """Serializer for vehicle selection and tax calculation"""
    vehicle_type = serializers.ChoiceField(
        choices=['VEHICLE', 'MOTORCYCLE', 'HEAVY_MACHINERY']
    )
    vehicle_id = serializers.IntegerField()
    import_type = serializers.ChoiceField(
        choices=['DIRECT', 'PREVIOUSLY_REGISTERED']
    )
    year_of_manufacture = serializers.IntegerField(
        min_value=1900,
        max_value=datetime.now().year
    )

    def validate(self, data):
        """Validate that the vehicle exists"""
        vehicle_type = data['vehicle_type']
        vehicle_id = data['vehicle_id']

        if vehicle_type == 'VEHICLE':
            if not Vehicle.objects.filter(id=vehicle_id).exists():
                raise serializers.ValidationError("Vehicle not found")
        elif vehicle_type == 'MOTORCYCLE':
            if not Motorcycle.objects.filter(id=vehicle_id).exists():
                raise serializers.ValidationError("Motorcycle not found")
        elif vehicle_type == 'HEAVY_MACHINERY':
            if not HeavyMachinery.objects.filter(id=vehicle_id).exists():
                raise serializers.ValidationError("Heavy Machinery not found")

        return data


class TaxCalculationResultSerializer(serializers.ModelSerializer):
    """Serializer for tax calculation results"""
    vehicle_details = serializers.SerializerMethodField()
    breakdown = serializers.SerializerMethodField()

    class Meta:
        model = TaxCalculation
        fields = [
            'calculation_reference',
            'vehicle_type',
            'vehicle_details',
            'import_type',
            'year_of_manufacture',
            'current_year',
            'original_crsp',
            'depreciation_rate',
            'depreciated_value',
            'breakdown',
            'total_taxes',
            'total_cost',
            'created_at'
        ]

    def get_vehicle_details(self, obj):
        """Get details of the specific vehicle"""
        if obj.vehicle_type == 'VEHICLE':
            vehicle = Vehicle.objects.get(id=obj.vehicle_id)
            return {
                'make': vehicle.make.name,
                'model': vehicle.model.name,
                'engine_capacity': vehicle.engine_capacity,
                'fuel_type': vehicle.fuel_type,
                'body_type': vehicle.body_type,
                'transmission': vehicle.transmission
            }
        elif obj.vehicle_type == 'MOTORCYCLE':
            motorcycle = Motorcycle.objects.get(id=obj.vehicle_id)
            return {
                'make': motorcycle.make.name,
                'model': motorcycle.model.name,
                'engine_capacity': motorcycle.engine_capacity,
                'fuel': motorcycle.fuel,
                'transmission': motorcycle.transmission
            }
        elif obj.vehicle_type == 'HEAVY_MACHINERY':
            machinery = HeavyMachinery.objects.get(id=obj.vehicle_id)
            return {
                'make': machinery.make.name,
                'model': machinery.model.name,
                'horsepower': machinery.horsepower
            }
        return {}

    def get_breakdown(self, obj):
        """Get tax breakdown"""
        breakdown = {
            'customs_value': float(obj.customs_value),
            'import_duty': float(obj.import_duty),
            'excise_value': float(obj.excise_value),
            'excise_duty': float(obj.excise_duty),
            'vat_value': float(obj.vat_value),
            'vat': float(obj.vat),
        }

        if obj.import_type == 'DIRECT':
            breakdown['rdl'] = float(obj.rdl)
            breakdown['idf'] = float(obj.idf)

        return breakdown


class SimpleCalculatorSerializer(serializers.Serializer):
    """For quick calculations without saving"""
    crsp = serializers.DecimalField(max_digits=15, decimal_places=2)
    vehicle_category = serializers.ChoiceField(
        choices=[
            ('VEHICLE_1500CC_BELOW', 'Vehicles ≤1500cc'),
            ('VEHICLE_ABOVE_1500CC', 'Vehicles >1500cc'),
            ('VEHICLE_LUXURY', 'Luxury Vehicles'),
            ('VEHICLE_ELECTRIC', 'Electric Vehicles'),
            ('MOTORCYCLE', 'Motorcycles'),
            ('HEAVY_MACHINERY', 'Heavy Machinery'),
            ('AMBULANCE', 'Ambulances'),
            ('SPECIAL_PURPOSE', 'Special Purpose'),
        ]
    )
    import_type = serializers.ChoiceField(
        choices=['DIRECT', 'PREVIOUSLY_REGISTERED']
    )
    year_of_manufacture = serializers.IntegerField(
        min_value=1900,
        max_value=datetime.now().year
    )
