# calculator/views.py - Updated TaxCalculatorService class

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from decimal import Decimal
from datetime import datetime
import uuid

from vehicles.models import Vehicle, Motorcycle, HeavyMachinery
from .models import TaxCalculation, VehicleCategory, DepreciationRate
from .serializers import (
    VehicleSelectionSerializer,
    TaxCalculationResultSerializer,
    SimpleCalculatorSerializer
)

class TaxCalculatorService:
    """Service class to handle tax calculations"""

    @staticmethod
    def get_depreciation_rate(import_type, years_old):
        """Get depreciation rate based on import type and age"""
        try:
            # Try to get the most specific rate (exact match or smallest range)
            rates = DepreciationRate.objects.filter(
                import_type=import_type,
                years_from__lte=years_old,
                years_to__gte=years_old
            ).order_by('years_from', '-years_to')

            if rates.exists():
                return rates.first().depreciation_percentage

        except Exception as e:
            print(f"Error getting depreciation rate from DB: {e}")

        # Fallback to hardcoded rates
        if import_type == 'DIRECT':
            if years_old <= 0:
                return Decimal('0')
            elif years_old <= 1:
                return Decimal('0')
            elif years_old <= 2:
                return Decimal('20')
            elif years_old <= 3:
                return Decimal('30')
            elif years_old <= 4:
                return Decimal('40')
            elif years_old <= 5:
                return Decimal('50')
            elif years_old <= 6:
                return Decimal('55')
            elif years_old <= 7:
                return Decimal('60')
            elif years_old <= 8:
                return Decimal('65')
            else:
                return Decimal('65')
        else:  # PREVIOUSLY_REGISTERED
            if years_old <= 0:
                return Decimal('0')
            elif years_old == 1:
                return Decimal('20')
            elif years_old == 2:
                return Decimal('35')
            elif years_old == 3:
                return Decimal('50')
            elif years_old == 4:
                return Decimal('60')
            elif years_old == 5:
                return Decimal('70')
            elif years_old == 6:
                return Decimal('75')
            elif years_old == 7:
                return Decimal('80')
            elif years_old == 8:
                return Decimal('83')
            elif years_old == 9:
                return Decimal('86')
            elif years_old == 10:
                return Decimal('89')
            elif years_old == 11:
                return Decimal('90')
            elif years_old == 12:
                return Decimal('91')
            elif years_old == 13:
                return Decimal('92')
            elif years_old == 14:
                return Decimal('93')
            elif years_old == 15:
                return Decimal('94')
            else:
                return Decimal('95')

    @staticmethod
    def determine_vehicle_category(vehicle_type, vehicle_id):
        """Determine the tax category based on vehicle characteristics"""
        if vehicle_type == 'MOTORCYCLE':
            return 'MOTORCYCLE'
        elif vehicle_type == 'HEAVY_MACHINERY':
            return 'HEAVY_MACHINERY'
        elif vehicle_type == 'VEHICLE':
            vehicle = Vehicle.objects.get(id=vehicle_id)

            # Check if it's electric
            if vehicle.fuel_type in ['ELECTRIC']:
                return 'VEHICLE_ELECTRIC'

            # Parse engine capacity - handle various formats
            engine_capacity_str = vehicle.engine_capacity
            try:
                # Remove non-numeric characters except dots
                engine_cc_str = ''.join(c for c in engine_capacity_str if c.isdigit() or c == '.')
                if engine_cc_str:
                    engine_cc = float(engine_cc_str)
                else:
                    engine_cc = 1500  # Default if parsing fails
            except:
                engine_cc = 1500  # Default if parsing fails

            # Determine category based on engine capacity and fuel type
            if engine_cc <= 1500:
                return 'VEHICLE_1500CC_BELOW'
            elif vehicle.fuel_type in ['GASOLINE', 'PETROL'] and engine_cc > 3000:
                return 'VEHICLE_LUXURY'
            elif vehicle.fuel_type == 'DIESEL' and engine_cc > 2500:
                return 'VEHICLE_LUXURY'
            else:
                return 'VEHICLE_ABOVE_1500CC'

        return 'VEHICLE_ABOVE_1500CC'  # Default

    @staticmethod
    def get_category_rates(category_name):
        """Get tax rates for a category"""
        try:
            category = VehicleCategory.objects.get(category=category_name)
            return category
        except VehicleCategory.DoesNotExist:
            # Default rates based on KRA guidelines
            defaults = {
                'VEHICLE_1500CC_BELOW': {
                    'import_duty_rate': Decimal('35'),
                    'excise_duty_rate': Decimal('20'),
                    'excise_duty_fixed': None,
                    'vat_rate': Decimal('16'),
                    'customs_value_percentage': Decimal('42.6')
                },
                'VEHICLE_ABOVE_1500CC': {
                    'import_duty_rate': Decimal('35'),
                    'excise_duty_rate': Decimal('25'),
                    'excise_duty_fixed': None,
                    'vat_rate': Decimal('16'),
                    'customs_value_percentage': Decimal('40.9')
                },
                'VEHICLE_LUXURY': {
                    'import_duty_rate': Decimal('35'),
                    'excise_duty_rate': Decimal('35'),
                    'excise_duty_fixed': None,
                    'vat_rate': Decimal('16'),
                    'customs_value_percentage': Decimal('37.8')
                },
                'VEHICLE_ELECTRIC': {
                    'import_duty_rate': Decimal('35'),
                    'excise_duty_rate': Decimal('10'),
                    'excise_duty_fixed': None,
                    'vat_rate': Decimal('16'),
                    'customs_value_percentage': Decimal('46.4')
                },
                'MOTORCYCLE': {
                    'import_duty_rate': Decimal('25'),
                    'excise_duty_rate': None,
                    'excise_duty_fixed': Decimal('12952.83'),
                    'vat_rate': Decimal('16'),
                    'customs_value_percentage': Decimal('55.2')
                },
                'HEAVY_MACHINERY': {
                    'import_duty_rate': Decimal('0'),
                    'excise_duty_rate': Decimal('0'),
                    'excise_duty_fixed': None,
                    'vat_rate': Decimal('16'),
                    'customs_value_percentage': Decimal('69')
                },
                'AMBULANCE': {
                    'import_duty_rate': Decimal('0'),
                    'excise_duty_rate': Decimal('25'),
                    'excise_duty_fixed': None,
                    'vat_rate': Decimal('16'),
                    'customs_value_percentage': Decimal('55.2')
                },
                'SPECIAL_PURPOSE': {
                    'import_duty_rate': Decimal('0'),
                    'excise_duty_rate': Decimal('0'),
                    'excise_duty_fixed': None,
                    'vat_rate': Decimal('16'),
                    'customs_value_percentage': Decimal('69')
                },
            }

            if category_name in defaults:
                rates = defaults[category_name]
                # Create a mock category object
                class MockCategory:
                    def __init__(self, data):
                        for key, value in data.items():
                            setattr(self, key, value)

                return MockCategory(rates)

            # Ultimate default
            return MockCategory({
                'import_duty_rate': Decimal('35'),
                'excise_duty_rate': Decimal('25'),
                'excise_duty_fixed': None,
                'vat_rate': Decimal('16'),
                'customs_value_percentage': Decimal('40.9')
            })

    @staticmethod
    def calculate_taxes(crsp, category_name, import_type, years_old):
        """Calculate all taxes based on inputs"""
        # Get depreciation rate
        depreciation_rate = TaxCalculatorService.get_depreciation_rate(import_type, years_old)

        # Calculate depreciated value
        depreciation_amount = crsp * (depreciation_rate / Decimal('100'))
        depreciated_value = crsp - depreciation_amount

        # Get category rates
        category = TaxCalculatorService.get_category_rates(category_name)

        # Calculate customs value
        customs_value = depreciated_value * (category.customs_value_percentage / Decimal('100'))

        # Calculate import duty
        import_duty = customs_value * (category.import_duty_rate / Decimal('100'))

        # Calculate excise value and duty
        excise_value = customs_value + import_duty

        if hasattr(category, 'excise_duty_fixed') and category.excise_duty_fixed:
            excise_duty = category.excise_duty_fixed
        elif hasattr(category, 'excise_duty_rate') and category.excise_duty_rate is not None:
            excise_duty = excise_value * (category.excise_duty_rate / Decimal('100'))
        else:
            excise_duty = Decimal('0')

        # Calculate VAT
        vat_value = excise_value + excise_duty
        vat = vat_value * (category.vat_rate / Decimal('100'))

        # Calculate additional fees for direct imports
        rdl = Decimal('0')
        idf = Decimal('0')

        if import_type == 'DIRECT':
            rdl = customs_value * Decimal('0.02')  # 2% of customs value
            idf = customs_value * Decimal('0.025')  # 2.5% of customs value

        # Calculate totals
        total_taxes = import_duty + excise_duty + vat + rdl + idf
        total_cost = depreciated_value + total_taxes

        return {
            'depreciation_rate': depreciation_rate,
            'depreciated_value': depreciated_value,
            'customs_value': customs_value,
            'import_duty': import_duty,
            'excise_value': excise_value,
            'excise_duty': excise_duty,
            'vat_value': vat_value,
            'vat': vat,
            'rdl': rdl,
            'idf': idf,
            'total_taxes': total_taxes,
            'total_cost': total_cost
        }


@api_view(['POST'])
def calculate_vehicle_tax(request):
    """Calculate tax for a selected vehicle"""
    serializer = VehicleSelectionSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    vehicle_type = data['vehicle_type']
    vehicle_id = data['vehicle_id']
    import_type = data['import_type']
    year_of_manufacture = data['year_of_manufacture']

    # Get vehicle and CRSP
    if vehicle_type == 'VEHICLE':
        vehicle = get_object_or_404(Vehicle, id=vehicle_id)
        crsp = vehicle.crsp
    elif vehicle_type == 'MOTORCYCLE':
        vehicle = get_object_or_404(Motorcycle, id=vehicle_id)
        crsp = vehicle.crsp
    else:  # HEAVY_MACHINERY
        vehicle = get_object_or_404(HeavyMachinery, id=vehicle_id)
        crsp = vehicle.crsp

    # Calculate vehicle age
    current_year = datetime.now().year
    years_old = current_year - year_of_manufacture

    # Determine category
    category_name = TaxCalculatorService.determine_vehicle_category(vehicle_type, vehicle_id)

    # Calculate taxes
    calculation = TaxCalculatorService.calculate_taxes(
        crsp, category_name, import_type, years_old
    )

    # Save calculation
    tax_calc = TaxCalculation.objects.create(
        vehicle_type=vehicle_type,
        vehicle_id=vehicle_id,
        import_type=import_type,
        year_of_manufacture=year_of_manufacture,
        current_year=current_year,
        original_crsp=crsp,
        depreciation_rate=calculation['depreciation_rate'],
        depreciated_value=calculation['depreciated_value'],
        customs_value=calculation['customs_value'],
        import_duty=calculation['import_duty'],
        excise_value=calculation['excise_value'],
        excise_duty=calculation['excise_duty'],
        vat_value=calculation['vat_value'],
        vat=calculation['vat'],
        rdl=calculation['rdl'],
        idf=calculation['idf'],
        total_taxes=calculation['total_taxes'],
        total_cost=calculation['total_cost'],
        calculation_reference=uuid.uuid4()
    )

    result_serializer = TaxCalculationResultSerializer(tax_calc)
    return Response(result_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
def quick_calculate(request):
    """Quick calculation without selecting a specific vehicle"""
    serializer = SimpleCalculatorSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    crsp = data['crsp']
    category_name = data['vehicle_category']
    import_type = data['import_type']
    year_of_manufacture = data['year_of_manufacture']

    # Calculate vehicle age
    current_year = datetime.now().year
    years_old = current_year - year_of_manufacture

    # Calculate taxes
    calculation = TaxCalculatorService.calculate_taxes(
        crsp, category_name, import_type, years_old
    )

    # Return results without saving
    return Response({
        'input': {
            'crsp': float(crsp),
            'category': category_name,
            'import_type': import_type,
            'year_of_manufacture': year_of_manufacture,
            'vehicle_age_years': years_old
        },
        'calculation': {
            'depreciation_rate': float(calculation['depreciation_rate']),
            'depreciated_value': float(calculation['depreciated_value']),
            'customs_value': float(calculation['customs_value']),
            'import_duty': float(calculation['import_duty']),
            'excise_value': float(calculation['excise_value']),
            'excise_duty': float(calculation['excise_duty']),
            'vat_value': float(calculation['vat_value']),
            'vat': float(calculation['vat']),
            'rdl': float(calculation['rdl']),
            'idf': float(calculation['idf']),
            'total_taxes': float(calculation['total_taxes']),
            'total_cost': float(calculation['total_cost'])
        }
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_calculation_history(request):
    """Get calculation history"""
    calculations = TaxCalculation.objects.all()[:20]  # Last 20 calculations
    serializer = TaxCalculationResultSerializer(calculations, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_calculation_by_reference(request, reference):
    """Get a specific calculation by reference"""
    calculation = get_object_or_404(TaxCalculation, calculation_reference=reference)
    serializer = TaxCalculationResultSerializer(calculation)
    return Response(serializer.data, status=status.HTTP_200_OK)
