# vehicles/filters.py
import django_filters
from .models import Vehicle, Motorcycle, HeavyMachinery

class VehicleFilter(django_filters.FilterSet):
    make_name = django_filters.CharFilter(field_name='make__name', lookup_expr='icontains')
    model_name = django_filters.CharFilter(field_name='model__name', lookup_expr='icontains')
    engine_capacity_min = django_filters.NumberFilter(field_name='engine_capacity', lookup_expr='gte')
    engine_capacity_max = django_filters.NumberFilter(field_name='engine_capacity', lookup_expr='lte')
    price_min = django_filters.NumberFilter(field_name='crsp', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='crsp', lookup_expr='lte')

    class Meta:
        model = Vehicle
        fields = [
            'make', 'model', 'transmission', 'drive_configuration',
            'body_type', 'fuel_type', 'seating'
        ]


class MotorcycleFilter(django_filters.FilterSet):
    make_name = django_filters.CharFilter(field_name='make__name', lookup_expr='icontains')
    model_name = django_filters.CharFilter(field_name='model__name', lookup_expr='icontains')
    price_min = django_filters.NumberFilter(field_name='crsp', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='crsp', lookup_expr='lte')

    class Meta:
        model = Motorcycle
        fields = ['make', 'model', 'transmission', 'fuel', 'seating']


class HeavyMachineryFilter(django_filters.FilterSet):
    make_name = django_filters.CharFilter(field_name='make__name', lookup_expr='icontains')
    model_name = django_filters.CharFilter(field_name='model__name', lookup_expr='icontains')
    price_min = django_filters.NumberFilter(field_name='crsp', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='crsp', lookup_expr='lte')

    class Meta:
        model = HeavyMachinery
        fields = ['make', 'model', 'horsepower']
