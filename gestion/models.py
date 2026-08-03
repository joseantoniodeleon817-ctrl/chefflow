"""
gestion/models.py

Define las 3 entidades principales del sistema ChefFlow:
Usuarios, Inventario y Pedidos, junto con sus relaciones.
"""

from django.db import models
from django.utils import timezone


class Usuario(models.Model):
    """
    Representa a los empleados del restaurante (meseros, cocineros, admin).
    NOTA: En producción real, se recomienda extender el modelo User de Django
    (AbstractUser) para aprovechar el sistema de autenticación nativo.
    Aquí se implementa como modelo simple para cumplir el requisito académico.
    """

    ROL_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('MESERO', 'Mesero'),
        ('COCINA', 'Cocina'),
        ('CAJERO', 'Cajero'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre completo")
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='MESERO')
    contrasena = models.CharField(max_length=128, verbose_name="Contraseña")
    # NOTA: En un sistema real, esto DEBE guardarse hasheado (ver make_password
    # de django.contrib.auth.hashers). Se deja en texto plano solo como
    # prototipo académico, documentar esta limitación en el informe.

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.nombre} ({self.get_rol_display()})"


class Inventario(models.Model):
    """
    Representa cada insumo/producto disponible en el restaurante.
    Es la base del Motor Predictivo de Inventario.
    """

    descripcion = models.CharField(max_length=200, verbose_name="Descripción del insumo")
    stock_actual = models.PositiveIntegerField(default=0, verbose_name="Stock actual")
    stock_minimo = models.PositiveIntegerField(default=5, verbose_name="Stock mínimo permitido")

    class Meta:
        db_table = 'inventario'
        verbose_name = 'Inventario'
        verbose_name_plural = 'Inventarios'

    def __str__(self):
        return f"{self.descripcion} - Stock: {self.stock_actual}"

    def esta_bajo_stock(self):
        """
        Método auxiliar del Motor Predictivo.
        Retorna True si el stock actual ya alcanzó o superó el límite mínimo.
        """
        return self.stock_actual <= self.stock_minimo


class Pedido(models.Model):
    """
    Representa una orden registrada en el Punto de Venta.
    Relaciona a un Usuario (mesero que lo registra) con un Insumo del Inventario.
    """

    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PREPARACION', 'En preparación'),
        ('LISTO', 'Listo'),
        ('ENTREGADO', 'Entregado'),
        ('CANCELADO', 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,  # Evita borrar usuarios con pedidos históricos
        related_name='pedidos',
        verbose_name="Usuario responsable"
    )
    # Relación con el insumo principal del pedido (para descontar inventario)
    insumo = models.ForeignKey(
        Inventario,
        on_delete=models.PROTECT,
        related_name='pedidos',
        verbose_name="Insumo solicitado"
    )
    mesa = models.PositiveIntegerField(verbose_name="Número de mesa")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad solicitada")
    fecha_hora = models.DateTimeField(default=timezone.now, verbose_name="Fecha y hora del pedido")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    class Meta:
        db_table = 'pedidos'
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-fecha_hora']  # Los más recientes primero

    def __str__(self):
        return f"Pedido #{self.id} - Mesa {self.mesa} - {self.estado}"
