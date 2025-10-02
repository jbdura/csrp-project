from decimal import Decimal
from datetime import date
from django.db.models import Q
from .models import VehicleCategory, DepreciationRate, TaxConfiguration
from vehicles.models import Vehicle, Motorcycle, HeavyMachinery


class TaxCalculationService:
    """
    Service class for calculating KRA import taxes
    Handles all vehicle types with their specific rules
    """

    def __init__(self):
        self.config = TaxConfiguration.get_active_config()
        if not self.config:
            raise ValueError("No active tax configuration found. Please configure tax settings in admin.")

    def calculate(self, **kwargs):
        """
        Main calculation method

        Args:
            vehicle_type: 'VEHICLE', 'MOTORCYCLE', or 'HEAVY_MACHINERY'
            vehicle_id: ID of vehicle from vehicles app (optional)
            market_value_kes: Current market value in KES
            year_of_manufacture: Year vehicle was made
            import_type: 'DIRECT' or 'PREVIOUSLY_REGISTERED'
            engine_capacity: Engine in cc (optional)
            fuel_type: Fuel type (optional, for category determination)
            category_type: Explicit category type (optional, auto-detected if not provided)

        Returns:
            dict: Complete tax breakdown
        """
        vehicle_type = kwargs.get('vehicle_type')
        vehicle_id = kwargs.get('vehicle_id')
        market_value_kes = Decimal(str(kwargs.get('market_value_kes')))
        year_of_manufacture = int(kwargs.get('year_of_manufacture'))
        import_type = kwargs.get('import_type')

        # Validate inputs
        self._validate_inputs(market_value_kes, year_of_manufacture, import_type)

        # Get vehicle details
        vehicle_details = self._get_vehicle_details(vehicle_type, vehicle_id)

        # Determine category
        category = self._determine_category(
            vehicle_type=vehicle_type,
            vehicle_details=vehicle_details,
            engine_capacity=kwargs.get('engine_capacity'),
            fuel_type=kwargs.get('fuel_type'),
            category_type=kwargs.get('category_type')
        )

        # Calculate age and depreciation
        vehicle_age = self.config.current_year - year_of_manufacture
        depreciation_rate = self._get_depreciation_rate(vehicle_age, import_type)

        # Step 1: Apply depreciation
        depreciated_value = market_value_kes * (Decimal('1') - depreciation_rate / Decimal('100'))

        # Step 2: Calculate customs value
        customs_value = depreciated_value * category.customs_factor

        # Step 3: Calculate import duty
        if category.exempt_import_duty:
            import_duty = Decimal('0')
        else:
            import_duty = customs_value * (category.import_duty_rate / Decimal('100'))

        # Step 4: Calculate excise value
        excise_value = customs_value + import_duty

        # Step 5: Calculate excise duty
        if category.exempt_excise_duty:
            excise_duty = Decimal('0')
        elif category.excise_duty_fixed_amount:
            # Motorcycles use fixed amount
            excise_duty = category.excise_duty_fixed_amount
        else:
            excise_duty = excise_value * (category.excise_duty_rate / Decimal('100'))

        # Step 6: Calculate VAT value
        vat_value = excise_value + excise_duty

        # Step 7: Calculate VAT
        vat = vat_value * (self.config.vat_rate / Decimal('100'))

        # Step 8: Calculate fees (only for direct imports)
        if import_type == 'DIRECT':
            idf = customs_value * (self.config.idf_rate / Decimal('100'))
            rdl = customs_value * (self.config.rdl_rate / Decimal('100'))
        else:
            idf = Decimal('0')
            rdl = Decimal('0')

        # Step 9: Total tax
        total_tax = import_duty + excise_duty + vat + idf + rdl

        # Step 10: Total cost
        total_cost = market_value_kes + total_tax

        # Additional estimated costs
        total_additional = self.config.total_estimated_additional_costs
        grand_total = total_cost + total_additional

        # Prepare breakdown
        breakdown = {
            'input_data': {
                'vehicle_type': vehicle_type,
                'market_value_kes': float(market_value_kes),
                'year_of_manufacture': year_of_manufacture,
                'import_type': import_type,
                'vehicle_details': vehicle_details,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'type': category.category_type,
                    'customs_factor': float(category.customs_factor),
                    'import_duty_rate': float(category.import_duty_rate),
                    'excise_duty_rate': float(category.excise_duty_rate) if category.excise_duty_rate else None,
                }
            },
            'calculation_steps': {
                '1_vehicle_age': vehicle_age,
                '2_depreciation_rate': float(depreciation_rate),
                '3_depreciated_value': float(depreciated_value),
                '4_customs_value': float(customs_value),
                '5_import_duty': float(import_duty),
                '6_excise_value': float(excise_value),
                '7_excise_duty': float(excise_duty),
                '8_vat_value': float(vat_value),
                '9_vat': float(vat),
                '10_idf': float(idf),
                '11_rdl': float(rdl),
            },
            'tax_breakdown': {
                'import_duty': float(import_duty),
                'excise_duty': float(excise_duty),
                'vat': float(vat),
                'idf': float(idf),
                'rdl': float(rdl),
                'total_tax': float(total_tax),
            },
            'summary': {
                'market_value': float(market_value_kes),
                'total_tax': float(total_tax),
                'total_cost': float(total_cost),
                'tax_percentage': float((total_tax / market_value_kes) * 100) if market_value_kes > 0 else 0,
            },
            'additional_costs_estimate': {
                'clearing_agent': float(self.config.estimated_clearing_agent_fee),
                'port_handling': float(self.config.estimated_port_handling),
                'ntsa_inspection': float(self.config.estimated_ntsa_inspection),
                'registration': float(self.config.estimated_registration),
                'transport': float(self.config.estimated_transport),
                'total_additional': float(total_additional),
            },
            'grand_total_estimate': float(grand_total),
        }

        # Get purchase cost (default to market_value if not provided)
        purchase_cost_kes = kwargs.get('purchase_cost_kes')
        if purchase_cost_kes:
            purchase_cost = Decimal(str(purchase_cost_kes))
        else:
            purchase_cost = market_value_kes  # If not provided, assume purchase = CRSP

        # Calculate actual total the user will pay
        actual_total_cost = purchase_cost + total_tax
        actual_grand_total = actual_total_cost + total_additional

        # Update the breakdown to include purchase cost
        breakdown['purchase_info'] = {
            'purchase_cost_kes': float(purchase_cost),
            'government_crsp': float(market_value_kes),
            'is_different': float(purchase_cost) != float(market_value_kes),
        }

        breakdown['summary']['purchase_cost'] = float(purchase_cost)
        breakdown['summary']['actual_total_cost'] = float(actual_total_cost)
        breakdown['grand_total_estimate'] = float(actual_grand_total)

        # Return data for saving
        return {
            'vehicle_age': vehicle_age,
            'depreciation_rate': depreciation_rate,
            'depreciated_value': depreciated_value,
            'customs_value': customs_value,
            'import_duty': import_duty,
            'excise_value': excise_value,
            'excise_duty': excise_duty,
            'vat_value': vat_value,
            'vat': vat,
            'idf': idf,
            'rdl': rdl,
            'total_tax': total_tax,
            'total_cost': total_cost,
            'category': category,
            'breakdown': breakdown,
            'vehicle_details': vehicle_details,
        }

    def _validate_inputs(self, market_value, year, import_type):
        """Validate calculation inputs"""
        if market_value <= 0:
            raise ValueError("Market value must be greater than 0")

        if year > self.config.current_year:
            raise ValueError(f"Year of manufacture cannot be in the future (current year: {self.config.current_year})")

        if year < 1990:
            raise ValueError("Year of manufacture must be 1990 or later")

        if import_type not in ['DIRECT', 'PREVIOUSLY_REGISTERED']:
            raise ValueError("Invalid import type. Must be 'DIRECT' or 'PREVIOUSLY_REGISTERED'")

        vehicle_age = self.config.current_year - year
        if import_type == 'DIRECT' and vehicle_age > 8:
            raise ValueError("Direct imports cannot exceed 8 years of age (Kenya regulation)")

    def _get_vehicle_details(self, vehicle_type, vehicle_id):
        """Fetch vehicle details from vehicles app"""
        if not vehicle_id:
            return {}

        try:
            if vehicle_type == 'VEHICLE':
                vehicle = Vehicle.objects.select_related('make', 'model').get(id=vehicle_id)
                return {
                    'make': vehicle.make.name,
                    'model': vehicle.model.name,
                    'engine_capacity': vehicle.engine_capacity,
                    'fuel_type': vehicle.fuel_type,
                    'body_type': vehicle.body_type,
                    'transmission': vehicle.transmission,
                    'crsp': float(vehicle.crsp),
                }
            elif vehicle_type == 'MOTORCYCLE':
                motorcycle = Motorcycle.objects.select_related('make', 'model').get(id=vehicle_id)
                return {
                    'make': motorcycle.make.name,
                    'model': motorcycle.model.name,
                    'engine_capacity': motorcycle.engine_capacity,
                    'fuel_type': motorcycle.fuel,
                    'crsp': float(motorcycle.crsp),
                }
            elif vehicle_type == 'HEAVY_MACHINERY':
                machinery = HeavyMachinery.objects.select_related('make', 'model').get(id=vehicle_id)
                return {
                    'make': machinery.make.name,
                    'model': machinery.model.name,
                    'horsepower': machinery.horsepower,
                    'crsp': float(machinery.crsp),
                }
        except (Vehicle.DoesNotExist, Motorcycle.DoesNotExist, HeavyMachinery.DoesNotExist):
            raise ValueError(f"Vehicle with ID {vehicle_id} not found")

        return {}

    def _determine_category(self, vehicle_type, vehicle_details, engine_capacity, fuel_type, category_type):
        """
        Intelligently determine vehicle category based on specifications
        """
        if category_type:
            # Explicit category provided
            try:
                return VehicleCategory.objects.get(
                    category_type=category_type,
                    is_active=True
                )
            except VehicleCategory.DoesNotExist:
                raise ValueError(f"Invalid category type: {category_type}")

        # Auto-detect category
        if vehicle_type == 'HEAVY_MACHINERY':
            return VehicleCategory.objects.get(
                category_type='HEAVY_MACHINERY',
                is_active=True
            )

        if vehicle_type == 'MOTORCYCLE':
            return VehicleCategory.objects.get(
                category_type='MOTORCYCLE',
                is_active=True
            )

        # For vehicles, determine by engine and fuel type
        engine_cc = engine_capacity or vehicle_details.get('engine_capacity')
        fuel = fuel_type or vehicle_details.get('fuel_type', '')

        # Convert engine to integer if it's a string
        if isinstance(engine_cc, str):
            # Extract digits from string like "1500cc" or "2000"
            engine_cc = int(''.join(filter(str.isdigit, engine_cc)) or '0')

        if not engine_cc:
            raise ValueError("Engine capacity is required for vehicle category determination")

        # Check for electric
        if fuel.upper() in ['ELECTRIC']:
            return VehicleCategory.objects.get(
                category_type='ELECTRIC_VEHICLE',
                is_active=True
            )

        # Check for hybrid
        if 'HYBRID' in fuel.upper():
            return VehicleCategory.objects.get(
                category_type='HYBRID_VEHICLE',
                is_active=True
            )

        # Check engine size for petrol/diesel
        if engine_cc <= 1500:
            return VehicleCategory.objects.get(
                category_type='PASSENGER_CAR_SMALL',
                is_active=True
            )
        elif engine_cc > 3000 and fuel.upper() in ['PETROL', 'GASOLINE']:
            return VehicleCategory.objects.get(
                category_type='PASSENGER_CAR_LARGE',
                is_active=True
            )
        elif engine_cc > 2500 and fuel.upper() == 'DIESEL':
            return VehicleCategory.objects.get(
                category_type='PASSENGER_CAR_LARGE',
                is_active=True
            )
        else:
            return VehicleCategory.objects.get(
                category_type='PASSENGER_CAR_MEDIUM',
                is_active=True
            )

    def _get_depreciation_rate(self, age, import_type):
        """Get depreciation rate from database"""
        try:
            dep_rate = DepreciationRate.objects.get(
                import_type=import_type,
                vehicle_age_years=age,
                is_active=True
            )
            return dep_rate.depreciation_rate
        except DepreciationRate.DoesNotExist:
            # If exact age not found, get the highest available for that import type
            if import_type == 'DIRECT':
                max_rate = DepreciationRate.objects.filter(
                    import_type=import_type,
                    is_active=True
                ).order_by('-depreciation_rate').first()
                return max_rate.depreciation_rate if max_rate else Decimal('65')
            else:
                # For previously registered, use max rate if age exceeds table
                max_rate = DepreciationRate.objects.filter(
                    import_type=import_type,
                    is_active=True
                ).order_by('-depreciation_rate').first()
                return max_rate.depreciation_rate if max_rate else Decimal('95')

    def compare_import_types(self, **kwargs):
        """
        Compare Direct Import vs Previously Registered costs
        Returns both calculations for comparison
        """
        # Calculate for DIRECT import
        direct_kwargs = {**kwargs, 'import_type': 'DIRECT'}
        direct_result = self.calculate(**direct_kwargs)

        # Calculate for PREVIOUSLY_REGISTERED
        prev_kwargs = {**kwargs, 'import_type': 'PREVIOUSLY_REGISTERED'}
        prev_result = self.calculate(**prev_kwargs)

        # Calculate savings
        savings = direct_result['total_tax'] - prev_result['total_tax']
        savings_percentage = (savings / direct_result['total_tax'] * 100) if direct_result['total_tax'] > 0 else 0

        return {
            'direct_import': direct_result['breakdown'],
            'previously_registered': prev_result['breakdown'],
            'comparison': {
                'tax_difference': float(savings),
                'savings_percentage': float(savings_percentage),
                'cheaper_option': 'Previously Registered' if savings > 0 else 'Direct Import',
                'recommendation': self._get_recommendation(savings, savings_percentage)
            }
        }

    def _get_recommendation(self, savings, savings_percentage):
        """Generate recommendation based on savings"""
        if savings > 100000:
            return f"Previously Registered saves you KES {savings:,.2f} ({savings_percentage:.1f}%). Significant savings!"
        elif savings > 0:
            return f"Previously Registered saves you KES {savings:,.2f} ({savings_percentage:.1f}%)."
        else:
            return "Direct Import and Previously Registered have similar costs."
