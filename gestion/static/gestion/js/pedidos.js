// gestion/static/gestion/js/pedidos.js

/**
 * Script básico de interactividad para el Punto de Venta.
 * Valida en el cliente que la cantidad solicitada no supere
 * el stock disponible del insumo seleccionado (validación previa,
 * la validación REAL y segura siempre ocurre en el backend).
 */

document.addEventListener('DOMContentLoaded', function () {
    const selectInsumo = document.getElementById('insumo_id');
    const inputCantidad = document.getElementById('cantidad');

    if (selectInsumo && inputCantidad) {
        selectInsumo.addEventListener('change', function () {
            const opcionSeleccionada = selectInsumo.options[selectInsumo.selectedIndex];
            const stockDisponible = opcionSeleccionada.getAttribute('data-stock');

            if (stockDisponible) {
                inputCantidad.setAttribute('max', stockDisponible);
                console.log(`Stock disponible para este insumo: ${stockDisponible}`);
            }
        });
    }

    // Validación previa al envío del formulario
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function (e) {
            const cantidad = parseInt(inputCantidad.value);
            const max = parseInt(inputCantidad.getAttribute('max'));

            if (max && cantidad > max) {
                e.preventDefault();
                alert(`La cantidad solicitada (${cantidad}) supera el stock disponible (${max}).`);
            }
        });
    }
});
