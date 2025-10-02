from django.urls import path
from . import views

app_name = 'tax_calculator'

urlpatterns = [
    # Main calculation endpoints
    path('calculate/', views.calculate_tax, name='calculate-tax'),
    path('save-calculation/', views.save_calculation, name='save-calculation'),
    path('compare/', views.compare_import_types, name='compare-import-types'),

    # Saved calculations
    path('calculations/', views.TaxCalculationListView.as_view(), name='list-calculations'),
    path('calculations/<uuid:calculation_id>/', views.get_calculation, name='get-calculation'),
    path('calculations/<uuid:calculation_id>/delete/', views.delete_calculation, name='delete-calculation'),

    # Reference data
    path('categories/', views.list_vehicle_categories, name='list-categories'),
    path('depreciation-rates/', views.list_depreciation_rates, name='list-depreciation-rates'),
    path('config/', views.get_tax_config, name='get-config'),
]
