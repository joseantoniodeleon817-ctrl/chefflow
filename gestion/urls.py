"""
gestion/urls.py

Rutas específicas de la app 'gestion'.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pedido/registrar/', views.registrar_pedido, name='registrar_pedido'),
    path('api/inventario/', views.api_estado_inventario, name='api_estado_inventario'),
]
