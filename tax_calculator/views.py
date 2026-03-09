from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework import generics
from django.core.exceptions import ValidationError
from .models import TaxCalculation, VehicleCategory, DepreciationRate, TaxConfiguration
from .services import TaxCalculationService
from .serializers import (
    TaxCalculationSerializer,
    TaxCalculationListSerializer,
    TaxCalculationInputSerializer,
    VehicleCategorySerializer,
    DepreciationRateSerializer,
    TaxConfigurationSerializer,
    ComparisonInputSerializer,
)


class CalculationRateThrottle(AnonRateThrottle):
    """Rate limiting for calculation endpoint"""
    rate = '100/hour'  # 100 requests per hour per IP


@api_view(['POST'])
@throttle_classes([CalculationRateThrottle])
def calculate_tax(request):
    """
    Calculate import tax for a vehicle
    Does NOT save to database unless explicitly requested
    """
    try:
        # Validate input
        input_serializer = TaxCalculationInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'Invalid input',
                    'details': input_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate
        service = TaxCalculationService()
        result = service.calculate(**input_serializer.validated_data)

        return Response({
            'success': True,
            'data': result['breakdown'],
            'message': 'Calculation completed successfully. Use /api/tax/save-calculation/ endpoint to save this result.'
        })

    except ValueError as e:
        return Response(
            {
                'success': False,
                'error': str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': 'An error occurred during calculation',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@throttle_classes([CalculationRateThrottle])
def save_calculation(request):
    """
    Save a tax calculation to database
    User explicitly requests to save
    """
    try:
        # Validate and calculate
        input_serializer = TaxCalculationInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'Invalid input',
                    'details': input_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate
        service = TaxCalculationService()
        result = service.calculate(**input_serializer.validated_data)

        # Save to database
        calculation = TaxCalculation.objects.create(
            vehicle_type=input_serializer.validated_data.get('vehicle_type'),
            vehicle_id=input_serializer.validated_data.get('vehicle_id'),
            market_value_kes=input_serializer.validated_data.get('market_value_kes'),
            year_of_manufacture=input_serializer.validated_data.get('year_of_manufacture'),
            engine_capacity=input_serializer.validated_data.get('engine_capacity'),
            import_type=input_serializer.validated_data.get('import_type'),
            vehicle_category=result['category'],
            make=result['vehicle_details'].get('make', ''),
            model=result['vehicle_details'].get('model', ''),
            fuel_type=result['vehicle_details'].get('fuel_type', ''),
            vehicle_age=result['vehicle_age'],
            depreciation_rate=result['depreciation_rate'],
            depreciated_value=result['depreciated_value'],
            customs_value=result['customs_value'],
            import_duty=result['import_duty'],
            excise_value=result['excise_value'],
            excise_duty=result['excise_duty'],
            vat_value=result['vat_value'],
            vat=result['vat'],
            idf=result['idf'],
            rdl=result['rdl'],
            total_tax=result['total_tax'],
            total_cost=result['total_cost'],
            calculation_breakdown=result['breakdown'],
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        output_serializer = TaxCalculationSerializer(calculation)

        return Response({
            'success': True,
            'message': 'Calculation saved successfully',
            'data': output_serializer.data
        }, status=status.HTTP_201_CREATED)

    except ValueError as e:
        return Response(
            {
                'success': False,
                'error': str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': 'An error occurred while saving calculation',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_calculation(request, calculation_id):
    """Retrieve a saved calculation by UUID"""
    try:
        calculation = TaxCalculation.objects.get(calculation_id=calculation_id)
        serializer = TaxCalculationSerializer(calculation)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except TaxCalculation.DoesNotExist:
        return Response(
            {
                'success': False,
                'error': 'Calculation not found'
            },
            status=status.HTTP_404_NOT_FOUND
        )


class TaxCalculationListView(generics.ListAPIView):
    """List all saved calculations with pagination"""
    queryset = TaxCalculation.objects.all().select_related('vehicle_category')
    serializer_class = TaxCalculationListSerializer

    def get_queryset(self):
        """Filter by vehicle type if provided"""
        queryset = super().get_queryset()
        vehicle_type = self.request.query_params.get('vehicle_type')
        import_type = self.request.query_params.get('import_type')

        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        if import_type:
            queryset = queryset.filter(import_type=import_type)

        return queryset


@api_view(['GET'])
def list_vehicle_categories(request):
    """List all active vehicle categories"""
    categories = VehicleCategory.objects.filter(is_active=True).order_by('name')
    serializer = VehicleCategorySerializer(categories, many=True)
    return Response({
        'success': True,
        'count': categories.count(),
        'data': serializer.data
    })


@api_view(['GET'])
def list_depreciation_rates(request):
    """List all active depreciation rates"""
    import_type = request.GET.get('import_type')

    rates = DepreciationRate.objects.filter(is_active=True)
    if import_type:
        rates = rates.filter(import_type=import_type)

    rates = rates.order_by('import_type', 'vehicle_age_years')
    serializer = DepreciationRateSerializer(rates, many=True)

    return Response({
        'success': True,
        'count': rates.count(),
        'data': serializer.data
    })


@api_view(['GET'])
def get_tax_config(request):
    """Get current tax configuration"""
    config = TaxConfiguration.get_active_config()

    if not config:
        return Response(
            {
                'success': False,
                'error': 'No active tax configuration found. Please contact administrator.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    serializer = TaxConfigurationSerializer(config)
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
@throttle_classes([CalculationRateThrottle])
def compare_import_types(request):
    """
    Compare Direct Import vs Previously Registered
    Returns both calculations side by side
    """
    try:
        # Validate input (same as calculate but without import_type)
        input_serializer = ComparisonInputSerializer(data=request.data)
        if not input_serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'error': 'Invalid input',
                    'details': input_serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Compare
        service = TaxCalculationService()
        comparison = service.compare_import_types(**input_serializer.validated_data)

        return Response({
            'success': True,
            'data': comparison,
            'message': 'Comparison completed successfully'
        })

    except ValueError as e:
        return Response(
            {
                'success': False,
                'error': str(e)
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {
                'success': False,
                'error': 'An error occurred during comparison',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
def delete_calculation(request, calculation_id):
    """Delete a saved calculation"""
    try:
        calculation = TaxCalculation.objects.get(calculation_id=calculation_id)
        calculation.delete()
        return Response({
            'success': True,
            'message': 'Calculation deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    except TaxCalculation.DoesNotExist:
        return Response(
            {
                'success': False,
                'error': 'Calculation not found'
            },
            status=status.HTTP_404_NOT_FOUND
        )
