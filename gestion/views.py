"""
gestion/views.py

Contiene la lógica de negocio de ChefFlow, incluyendo el
Motor Predictivo de Inventario que se ejecuta al registrar un pedido.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.http import JsonResponse

from .models import Usuario, Inventario, Pedido


def index(request):
    """
    Vista principal del Punto de Venta.
    Muestra el formulario para registrar pedidos y el listado de insumos disponibles.
    """
    usuarios = Usuario.objects.all()
    insumos = Inventario.objects.all()
    pedidos_recientes = Pedido.objects.select_related('usuario', 'insumo').all()[:10]

    contexto = {
        'usuarios': usuarios,
        'insumos': insumos,
        'pedidos_recientes': pedidos_recientes,
    }
    return render(request, 'gestion/index.html', contexto)


@require_http_methods(["POST"])
def registrar_pedido(request):
    """
    Vista encargada de:
    1. Registrar un nuevo pedido en la base de datos.
    2. Descontar el stock del inventario correspondiente.
    3. Ejecutar el Motor Predictivo de Inventario:
       Si stock_actual <= stock_minimo tras el descuento, se genera una alerta.

    Se usa una transacción atómica para garantizar consistencia:
    si algo falla, no se descuenta stock ni se crea el pedido a medias.
    """

    try:
        # --- 1. Recolección y validación de datos del formulario ---
        usuario_id = request.POST.get('usuario_id')
        insumo_id = request.POST.get('insumo_id')
        mesa = request.POST.get('mesa')
        cantidad = int(request.POST.get('cantidad', 1))

        if not all([usuario_id, insumo_id, mesa]):
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect('index')

        if cantidad <= 0:
            messages.error(request, "La cantidad debe ser mayor a cero.")
            return redirect('index')

        # --- 2. Transacción atómica: todo o nada ---
        with transaction.atomic():

            usuario = Usuario.objects.get(id=usuario_id)
            # select_for_update() bloquea la fila para evitar condiciones de
            # carrera si dos pedidos se registran simultáneamente.
            insumo = Inventario.objects.select_for_update().get(id=insumo_id)

            # --- Validación de negocio: no permitir pedidos sin stock ---
            if insumo.stock_actual < cantidad:
                messages.error(
                    request,
                    f"Stock insuficiente para '{insumo.descripcion}'. "
                    f"Disponible: {insumo.stock_actual}, solicitado: {cantidad}."
                )
                return redirect('index')

            # --- 3. Crear el pedido ---
            pedido = Pedido.objects.create(
                usuario=usuario,
                insumo=insumo,
                mesa=mesa,
                cantidad=cantidad,
                estado='PENDIENTE'
            )

            # --- 4. Descontar del inventario ---
            insumo.stock_actual -= cantidad
            insumo.save()

            # ==========================================================
            # === MOTOR PREDICTIVO DE INVENTARIO (COMPONENTE INNOVADOR) ===
            # ==========================================================
            # Tras el descuento, se evalúa si el stock llegó a un nivel
            # crítico. Esta es la regla de negocio central del proyecto.
            if insumo.esta_bajo_stock():
                messages.warning(
                    request,
                    f"⚠️ ALERTA DE INVENTARIO: '{insumo.descripcion}' "
                    f"alcanzó el stock mínimo (Actual: {insumo.stock_actual}, "
                    f"Mínimo: {insumo.stock_minimo}). Se recomienda reabastecer."
                )
            else:
                messages.success(
                    request,
                    f"Pedido #{pedido.id} registrado correctamente para la mesa {mesa}."
                )

        return redirect('index')

    except Usuario.DoesNotExist:
        messages.error(request, "El usuario seleccionado no existe.")
        return redirect('index')
    except Inventario.DoesNotExist:
        messages.error(request, "El insumo seleccionado no existe.")
        return redirect('index')
    except ValueError:
        messages.error(request, "Datos inválidos en el formulario.")
        return redirect('index')
    except Exception as e:
        # Captura genérica para prototipo; en producción se debe loguear
        # el error con un sistema como Sentry o logging estructurado.
        messages.error(request, f"Error inesperado: {str(e)}")
        return redirect('index')


def api_estado_inventario(request):
    """
    Endpoint auxiliar (opcional) que retorna en JSON el estado del inventario.
    Útil para consumir desde JavaScript y mostrar alertas dinámicas
    sin recargar la página (mejora de UX para el frontend).
    """
    insumos = Inventario.objects.all()
    data = [
        {
            'id': i.id,
            'descripcion': i.descripcion,
            'stock_actual': i.stock_actual,
            'stock_minimo': i.stock_minimo,
            'alerta': i.esta_bajo_stock(),
        }
        for i in insumos
    ]
    return JsonResponse({'inventario': data})
