from django.urls import path
from . import views

urlpatterns = [
    path('api/calculate-radius/', views.calculate_radius, name='calculate-radius'),
    path('api/calculate-research-radii/', views.calculate_research_radii, name='calculate-research-radii'),
    path('api/health/', views.health_check, name='health-check'),
]