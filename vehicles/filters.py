# vehicles/filters.py
import django_filters
from .models import Vehicle, Motorcycle, HeavyMachinery

class VehicleFilter(django_filters.FilterSet):
    # Text filters
    make_name = django_filters.CharFilter(field_name='make__name', lookup_expr='icontains')
    model_name = django_filters.CharFilter(field_name='model__name', lookup_expr='icontains')
    model_number = django_filters.CharFilter(lookup_expr='icontains')

    # Engine capacity filters
    engine_capacity = django_filters.CharFilter(lookup_expr='icontains')
    engine_capacity_min = django_filters.NumberFilter(field_name='engine_capacity', lookup_expr='gte')
    engine_capacity_max = django_filters.NumberFilter(field_name='engine_capacity', lookup_expr='lte')

    # Price filters
    price_min = django_filters.NumberFilter(field_name='crsp', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='crsp', lookup_expr='lte')

    # Seating filters
    seating_min = django_filters.NumberFilter(field_name='seating', lookup_expr='gte')
    seating_max = django_filters.NumberFilter(field_name='seating', lookup_expr='lte')

    # GVW filter
    gvw = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Vehicle
        fields = {
            'make': ['exact'],
            'model': ['exact'],
            'transmission': ['exact'],
            'drive_configuration': ['exact'],
            'body_type': ['exact'],
            'fuel_type': ['exact'],
            'seating': ['exact'],
        }


class MotorcycleFilter(django_filters.FilterSet):
    # Text filters
    make_name = django_filters.CharFilter(field_name='make__name', lookup_expr='icontains')
    model_name = django_filters.CharFilter(field_name='model__name', lookup_expr='icontains')
    model_number = django_filters.CharFilter(lookup_expr='icontains')

    # Engine capacity filters
    engine_capacity = django_filters.CharFilter(lookup_expr='icontains')

    # Price filters
    price_min = django_filters.NumberFilter(field_name='crsp', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='crsp', lookup_expr='lte')

    # Seating filters
    seating_min = django_filters.NumberFilter(field_name='seating', lookup_expr='gte')
    seating_max = django_filters.NumberFilter(field_name='seating', lookup_expr='lte')

    class Meta:
        model = Motorcycle
        fields = {
            'make': ['exact'],
            'model': ['exact'],
            'transmission': ['exact'],
            'fuel': ['exact'],
            'seating': ['exact'],
        }


class HeavyMachineryFilter(django_filters.FilterSet):
    # Text filters
    make_name = django_filters.CharFilter(field_name='make__name', lookup_expr='icontains')
    model_name = django_filters.CharFilter(field_name='model__name', lookup_expr='icontains')
    horsepower = django_filters.CharFilter(lookup_expr='icontains')

    # Price filters
    price_min = django_filters.NumberFilter(field_name='crsp', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='crsp', lookup_expr='lte')

    class Meta:
        model = HeavyMachinery
        fields = {
            'make': ['exact'],
            'model': ['exact'],
        }
