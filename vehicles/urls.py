# vehicles/urls.py
from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    # Vehicle endpoints
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle-list'),
    path('vehicles/<int:pk>/', views.VehicleDetailView.as_view(), name='vehicle-detail'),
    path('vehicles/makes/', views.VehicleMakeListView.as_view(), name='vehicle-make-list'),
    path('vehicles/models/', views.VehicleModelListView.as_view(), name='vehicle-model-list'),

    # Motorcycle endpoints
    path('motorcycles/', views.MotorcycleListView.as_view(), name='motorcycle-list'),
    path('motorcycles/<int:pk>/', views.MotorcycleDetailView.as_view(), name='motorcycle-detail'),
    path('motorcycles/makes/', views.MotorcycleMakeListView.as_view(), name='motorcycle-make-list'),
    path('motorcycles/models/', views.MotorcycleModelListView.as_view(), name='motorcycle-model-list'),

    # Heavy Machinery endpoints
    path('machinery/', views.HeavyMachineryListView.as_view(), name='machinery-list'),
    path('machinery/<int:pk>/', views.HeavyMachineryDetailView.as_view(), name='machinery-detail'),
    path('machinery/makes/', views.HeavyMachineryMakeListView.as_view(), name='machinery-make-list'),
    path('machinery/models/', views.HeavyMachineryModelListView.as_view(), name='machinery-model-list'),

    # Unified search and options
    path('search/', views.unified_search, name='unified-search'),
    path('filter-options/', views.get_filter_options, name='filter-options'),

    # counts
    path('counts/', views.get_counts, name='counts'),
]
