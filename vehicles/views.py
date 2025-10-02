# vehicles/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import (
    VehicleMake, VehicleModel, Vehicle,
    MotorcycleMake, MotorcycleModel, Motorcycle,
    HeavyMachineryMake, HeavyMachineryModel, HeavyMachinery
)
from .serializers import (
    VehicleMakeSerializer, VehicleModelSerializer,
    VehicleListSerializer, VehicleDetailSerializer,
    MotorcycleMakeSerializer, MotorcycleModelSerializer,
    MotorcycleListSerializer, MotorcycleDetailSerializer,
    HeavyMachineryMakeSerializer, HeavyMachineryModelSerializer,
    HeavyMachineryListSerializer, HeavyMachineryDetailSerializer,
    VehicleSearchSerializer
)

# Custom cursor pagination for better performance with large datasets
class VehicleCursorPagination(CursorPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = 'id'  # Ensure consistent ordering


# ============== VEHICLE VIEWS ==============

class VehicleMakeListView(generics.ListAPIView):
    """List all vehicle makes"""
    queryset = VehicleMake.objects.all().order_by('name')
    serializer_class = VehicleMakeSerializer
    pagination_class = None


class VehicleModelListView(generics.ListAPIView):
    """List vehicle models, optionally filtered by make"""
    serializer_class = VehicleModelSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = VehicleModel.objects.select_related('make').order_by('make__name', 'name')
        make_id = self.request.query_params.get('make_id', None)
        if make_id:
            queryset = queryset.filter(make_id=make_id)
        return queryset


class VehicleListView(generics.ListAPIView):
    """List all vehicles with filtering and search"""
    queryset = Vehicle.objects.select_related('make', 'model').order_by('id')
    serializer_class = VehicleListSerializer
    pagination_class = VehicleCursorPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = {
        'make': ['exact'],
        'model': ['exact'],
        'transmission': ['exact'],
        'drive_configuration': ['exact'],
        'body_type': ['exact'],
        'fuel_type': ['exact'],
        'engine_capacity': ['exact', 'gte', 'lte'],
        'crsp': ['gte', 'lte'],
        'seating': ['exact', 'gte', 'lte'],
    }

    search_fields = ['make__name', 'model__name', 'model_number']
    ordering_fields = ['id', 'crsp', 'make__name', 'model__name']


class VehicleDetailView(generics.RetrieveAPIView):
    """Get details of a specific vehicle"""
    queryset = Vehicle.objects.select_related('make', 'model')
    serializer_class = VehicleDetailSerializer


# ============== MOTORCYCLE VIEWS ==============

class MotorcycleMakeListView(generics.ListAPIView):
    """List all motorcycle makes"""
    queryset = MotorcycleMake.objects.all().order_by('name')
    serializer_class = MotorcycleMakeSerializer
    pagination_class = None


class MotorcycleModelListView(generics.ListAPIView):
    """List motorcycle models, optionally filtered by make"""
    serializer_class = MotorcycleModelSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = MotorcycleModel.objects.select_related('make').order_by('make__name', 'name')
        make_id = self.request.query_params.get('make_id', None)
        if make_id:
            queryset = queryset.filter(make_id=make_id)
        return queryset


class MotorcycleListView(generics.ListAPIView):
    """List all motorcycles with filtering and search"""
    queryset = Motorcycle.objects.select_related('make', 'model').order_by('id')
    serializer_class = MotorcycleListSerializer
    pagination_class = VehicleCursorPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = {
        'make': ['exact'],
        'model': ['exact'],
        'transmission': ['exact'],
        'fuel': ['exact'],
        'engine_capacity': ['exact', 'gte', 'lte'],
        'crsp': ['gte', 'lte'],
        'seating': ['exact', 'gte', 'lte'],
    }

    search_fields = ['make__name', 'model__name', 'model_number']
    ordering_fields = ['id', 'crsp', 'make__name', 'model__name']


class MotorcycleDetailView(generics.RetrieveAPIView):
    """Get details of a specific motorcycle"""
    queryset = Motorcycle.objects.select_related('make', 'model')
    serializer_class = MotorcycleDetailSerializer


# ============== HEAVY MACHINERY VIEWS ==============

class HeavyMachineryMakeListView(generics.ListAPIView):
    """List all heavy machinery makes"""
    queryset = HeavyMachineryMake.objects.all().order_by('name')
    serializer_class = HeavyMachineryMakeSerializer
    pagination_class = None


class HeavyMachineryModelListView(generics.ListAPIView):
    """List heavy machinery models, optionally filtered by make"""
    serializer_class = HeavyMachineryModelSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = HeavyMachineryModel.objects.select_related('make').order_by('make__name', 'name')
        make_id = self.request.query_params.get('make_id', None)
        if make_id:
            queryset = queryset.filter(make_id=make_id)
        return queryset


class HeavyMachineryListView(generics.ListAPIView):
    """List all heavy machinery with filtering and search"""
    queryset = HeavyMachinery.objects.select_related('make', 'model').order_by('id')
    serializer_class = HeavyMachineryListSerializer
    pagination_class = VehicleCursorPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    filterset_fields = {
        'make': ['exact'],
        'model': ['exact'],
        'horsepower': ['exact', 'icontains'],
        'crsp': ['gte', 'lte'],
    }

    search_fields = ['make__name', 'model__name', 'horsepower']
    ordering_fields = ['id', 'crsp', 'make__name', 'model__name']


class HeavyMachineryDetailView(generics.RetrieveAPIView):
    """Get details of a specific heavy machinery"""
    queryset = HeavyMachinery.objects.select_related('make', 'model')
    serializer_class = HeavyMachineryDetailSerializer


# ============== UNIFIED SEARCH VIEW ==============

@api_view(['GET'])
def unified_search(request):
    """
    Unified search across all vehicle types with cursor pagination support
    """
    query = request.GET.get('q', '')
    vehicle_type = request.GET.get('type', '')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    fuel_type = request.GET.get('fuel_type')
    body_type = request.GET.get('body_type')
    transmission = request.GET.get('transmission')

    # For unified search, return all results (no pagination for search endpoint)
    results = []

    # Search vehicles
    if not vehicle_type or vehicle_type == 'vehicle':
        vehicle_qs = Vehicle.objects.select_related('make', 'model')

        if query:
            vehicle_qs = vehicle_qs.filter(
                Q(make__name__icontains=query) |
                Q(model__name__icontains=query) |
                Q(model_number__icontains=query)
            )

        if min_price:
            vehicle_qs = vehicle_qs.filter(crsp__gte=min_price)
        if max_price:
            vehicle_qs = vehicle_qs.filter(crsp__lte=max_price)
        if fuel_type:
            vehicle_qs = vehicle_qs.filter(fuel_type=fuel_type)
        if body_type:
            vehicle_qs = vehicle_qs.filter(body_type=body_type)
        if transmission:
            vehicle_qs = vehicle_qs.filter(transmission=transmission)

        for vehicle in vehicle_qs[:100]:
            results.append({
                'id': vehicle.id,
                'type': 'vehicle',
                'make': vehicle.make.name,
                'model': vehicle.model.name,
                'details': f"{vehicle.engine_capacity} {vehicle.get_fuel_type_display()} {vehicle.get_transmission_display()}",
                'crsp': vehicle.crsp,
                'formatted_price': vehicle.formatted_price,
                'engine_capacity': vehicle.engine_capacity,
                'fuel_type': vehicle.fuel_type,
                'body_type': vehicle.body_type,
                'transmission': vehicle.transmission,
            })

    # Search motorcycles
    if not vehicle_type or vehicle_type == 'motorcycle':
        motorcycle_qs = Motorcycle.objects.select_related('make', 'model')

        if query:
            motorcycle_qs = motorcycle_qs.filter(
                Q(make__name__icontains=query) |
                Q(model__name__icontains=query) |
                Q(model_number__icontains=query)
            )

        if min_price:
            motorcycle_qs = motorcycle_qs.filter(crsp__gte=min_price)
        if max_price:
            motorcycle_qs = motorcycle_qs.filter(crsp__lte=max_price)
        if transmission:
            motorcycle_qs = motorcycle_qs.filter(transmission=transmission)

        for motorcycle in motorcycle_qs[:100]:
            results.append({
                'id': motorcycle.id,
                'type': 'motorcycle',
                'make': motorcycle.make.name,
                'model': motorcycle.model.name,
                'details': f"{motorcycle.engine_capacity or 'N/A'} {motorcycle.get_fuel_display()}",
                'crsp': motorcycle.crsp,
                'formatted_price': motorcycle.formatted_price,
                'engine_capacity': motorcycle.engine_capacity,
                'fuel_type': motorcycle.fuel,
                'transmission': motorcycle.transmission,
            })

    # Search heavy machinery
    if not vehicle_type or vehicle_type == 'heavy_machinery':
        machinery_qs = HeavyMachinery.objects.select_related('make', 'model')

        if query:
            machinery_qs = machinery_qs.filter(
                Q(make__name__icontains=query) |
                Q(model__name__icontains=query) |
                Q(horsepower__icontains=query)
            )

        if min_price:
            machinery_qs = machinery_qs.filter(crsp__gte=min_price)
        if max_price:
            machinery_qs = machinery_qs.filter(crsp__lte=max_price)

        for machinery in machinery_qs[:100]:
            results.append({
                'id': machinery.id,
                'type': 'heavy_machinery',
                'make': machinery.make.name,
                'model': machinery.model.name,
                'details': f"{machinery.horsepower}",
                'crsp': machinery.crsp,
                'formatted_price': machinery.formatted_price,
            })

    results.sort(key=lambda x: x['crsp'])
    serializer = VehicleSearchSerializer(results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_filter_options(request):
    """Get all available filter options for dropdowns"""
    vehicle_transmissions = Vehicle.TRANSMISSION_CHOICES
    vehicle_drive_configs = Vehicle.DRIVE_CONFIG_CHOICES
    vehicle_body_types = Vehicle.BODY_TYPE_CHOICES
    vehicle_fuel_types = Vehicle.FUEL_TYPE_CHOICES

    motorcycle_transmissions = Motorcycle.MOTORCYCLE_TRANSMISSION_CHOICES
    motorcycle_fuel_types = Motorcycle.MOTORCYCLE_FUEL_CHOICES

    vehicle_prices = Vehicle.objects.values_list('crsp', flat=True)
    motorcycle_prices = Motorcycle.objects.values_list('crsp', flat=True)
    machinery_prices = HeavyMachinery.objects.values_list('crsp', flat=True)

    all_prices = list(vehicle_prices) + list(motorcycle_prices) + list(machinery_prices)
    min_price = min(all_prices) if all_prices else 0
    max_price = max(all_prices) if all_prices else 0

    return Response({
        'vehicle_options': {
            'transmissions': [{'value': k, 'label': v} for k, v in vehicle_transmissions],
            'drive_configurations': [{'value': k, 'label': v} for k, v in vehicle_drive_configs],
            'body_types': [{'value': k, 'label': v} for k, v in vehicle_body_types],
            'fuel_types': [{'value': k, 'label': v} for k, v in vehicle_fuel_types],
        },
        'motorcycle_options': {
            'transmissions': [{'value': k, 'label': v} for k, v in motorcycle_transmissions],
            'fuel_types': [{'value': k, 'label': v} for k, v in motorcycle_fuel_types],
        },
        'price_range': {
            'min': float(min_price),
            'max': float(max_price),
        }
    })
