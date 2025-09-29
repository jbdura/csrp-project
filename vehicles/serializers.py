# vehicles/serializers.py
from rest_framework import serializers
from .models import (
    VehicleMake, VehicleModel, Vehicle,
    MotorcycleMake, MotorcycleModel, Motorcycle,
    HeavyMachineryMake, HeavyMachineryModel, HeavyMachinery
)

# ============== VEHICLE SERIALIZERS ==============

class VehicleMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleMake
        fields = ['id', 'name']


class VehicleModelSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.name', read_only=True)

    class Meta:
        model = VehicleModel
        fields = ['id', 'make', 'make_name', 'name', 'model_number']


class VehicleListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing vehicles"""
    make_name = serializers.CharField(source='make.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    transmission_display = serializers.CharField(source='get_transmission_display', read_only=True)
    drive_configuration_display = serializers.CharField(source='get_drive_configuration_display', read_only=True)
    body_type_display = serializers.CharField(source='get_body_type_display', read_only=True)
    fuel_type_display = serializers.CharField(source='get_fuel_type_display', read_only=True)
    formatted_price = serializers.CharField(read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'make_name', 'model_name', 'model_number',
            'transmission', 'transmission_display',
            'drive_configuration', 'drive_configuration_display',
            'engine_capacity', 'body_type', 'body_type_display',
            'fuel_type', 'fuel_type_display',
            'seating', 'gvw', 'crsp', 'formatted_price'
        ]


class VehicleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single vehicle"""
    make = VehicleMakeSerializer(read_only=True)
    model = VehicleModelSerializer(read_only=True)
    transmission_display = serializers.CharField(source='get_transmission_display', read_only=True)
    drive_configuration_display = serializers.CharField(source='get_drive_configuration_display', read_only=True)
    body_type_display = serializers.CharField(source='get_body_type_display', read_only=True)
    fuel_type_display = serializers.CharField(source='get_fuel_type_display', read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    crsp_in_cents = serializers.IntegerField(read_only=True)

    class Meta:
        model = Vehicle
        fields = '__all__'


# ============== MOTORCYCLE SERIALIZERS ==============

class MotorcycleMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotorcycleMake
        fields = ['id', 'name']


class MotorcycleModelSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.name', read_only=True)

    class Meta:
        model = MotorcycleModel
        fields = ['id', 'make', 'make_name', 'name', 'model_number']


class MotorcycleListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing motorcycles"""
    make_name = serializers.CharField(source='make.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    transmission_display = serializers.CharField(source='get_transmission_display', read_only=True)
    fuel_display = serializers.CharField(source='get_fuel_display', read_only=True)
    formatted_price = serializers.CharField(read_only=True)

    class Meta:
        model = Motorcycle
        fields = [
            'id', 'make_name', 'model_name', 'model_number',
            'transmission', 'transmission_display',
            'engine_capacity', 'seating',
            'fuel', 'fuel_display',
            'crsp', 'formatted_price'
        ]


class MotorcycleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single motorcycle"""
    make = MotorcycleMakeSerializer(read_only=True)
    model = MotorcycleModelSerializer(read_only=True)
    transmission_display = serializers.CharField(source='get_transmission_display', read_only=True)
    fuel_display = serializers.CharField(source='get_fuel_display', read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    crsp_in_cents = serializers.IntegerField(read_only=True)

    class Meta:
        model = Motorcycle
        fields = '__all__'


# ============== HEAVY MACHINERY SERIALIZERS ==============

class HeavyMachineryMakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeavyMachineryMake
        fields = ['id', 'name']


class HeavyMachineryModelSerializer(serializers.ModelSerializer):
    make_name = serializers.CharField(source='make.name', read_only=True)

    class Meta:
        model = HeavyMachineryModel
        fields = ['id', 'make', 'make_name', 'name']


class HeavyMachineryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing heavy machinery"""
    make_name = serializers.CharField(source='make.name', read_only=True)
    model_name = serializers.CharField(source='model.name', read_only=True)
    formatted_price = serializers.CharField(read_only=True)

    class Meta:
        model = HeavyMachinery
        fields = [
            'id', 'make_name', 'model_name',
            'horsepower', 'crsp', 'formatted_price'
        ]


class HeavyMachineryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single heavy machinery"""
    make = HeavyMachineryMakeSerializer(read_only=True)
    model = HeavyMachineryModelSerializer(read_only=True)
    formatted_price = serializers.CharField(read_only=True)
    crsp_in_cents = serializers.IntegerField(read_only=True)

    class Meta:
        model = HeavyMachinery
        fields = '__all__'


# ============== SEARCH SERIALIZERS ==============

class VehicleSearchSerializer(serializers.Serializer):
    """Unified search results serializer"""
    id = serializers.IntegerField()
    type = serializers.CharField()  # 'vehicle', 'motorcycle', 'heavy_machinery'
    make = serializers.CharField()
    model = serializers.CharField()
    details = serializers.CharField()
    crsp = serializers.DecimalField(max_digits=15, decimal_places=2)
    formatted_price = serializers.CharField()

    # Additional fields for filtering
    engine_capacity = serializers.CharField(required=False, allow_null=True)
    fuel_type = serializers.CharField(required=False, allow_null=True)
    body_type = serializers.CharField(required=False, allow_null=True)
    transmission = serializers.CharField(required=False, allow_null=True)
