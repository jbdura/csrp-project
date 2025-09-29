# calculator/urls.py
from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    path('calculate/', views.calculate_vehicle_tax, name='calculate-vehicle-tax'),
    path('quick-calculate/', views.quick_calculate, name='quick-calculate'),
    path('history/', views.get_calculation_history, name='calculation-history'),
    path('calculation/<uuid:reference>/', views.get_calculation_by_reference, name='calculation-detail'),
]
