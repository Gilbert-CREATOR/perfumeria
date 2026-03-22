// Filtros Avanzados JavaScript
var minPrice = 0;
var maxPrice = 500;
var isDragging = false;
var currentThumb = null;

// Inicializar slider de precio
function initPriceSlider() {
    var minThumb = document.getElementById('minThumb');
    var maxThumb = document.getElementById('maxThumb');
    var sliderRange = document.getElementById('sliderRange');
    var minValue = document.getElementById('minValue');
    var maxValue = document.getElementById('maxValue');
    var minInput = document.getElementById('minPriceInput');
    var maxInput = document.getElementById('maxPriceInput');
    
    // Eventos para thumb mínimo
    minThumb.addEventListener('mousedown', function(e) {
        isDragging = true;
        currentThumb = 'min';
        e.preventDefault();
    });
    
    // Eventos para thumb máximo
    maxThumb.addEventListener('mousedown', function(e) {
        isDragging = true;
        currentThumb = 'max';
        e.preventDefault();
    });
    
    // Eventos globales
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    // Eventos de inputs
    minInput.addEventListener('input', function() {
        var value = parseInt(this.value) || 0;
        if (value >= 0 && value <= maxPrice) {
            minPrice = value;
            updateSlider();
        }
    });
    
    maxInput.addEventListener('input', function() {
        var value = parseInt(this.value) || 500;
        if (value >= minPrice && value <= 500) {
            maxPrice = value;
            updateSlider();
        }
    });
}

// Manejar movimiento del mouse
function handleMouseMove(e) {
    if (!isDragging) return;
    
    var slider = document.getElementById('priceSlider');
    var rect = slider.getBoundingClientRect();
    var x = e.clientX - rect.left;
    var percentage = (x / rect.width) * 100;
    
    if (percentage < 0) percentage = 0;
    if (percentage > 100) percentage = 100;
    
    var value = Math.round((percentage / 100) * 500);
    
    if (currentThumb === 'min') {
        if (value <= maxPrice) {
            minPrice = value;
            updateSlider();
        }
    } else if (currentThumb === 'max') {
        if (value >= minPrice) {
            maxPrice = value;
            updateSlider();
        }
    }
}

// Manejar liberación del mouse
function handleMouseUp() {
    isDragging = false;
    currentThumb = null;
}

// Actualizar slider
function updateSlider() {
    var minThumb = document.getElementById('minThumb');
    var maxThumb = document.getElementById('maxThumb');
    var sliderRange = document.getElementById('sliderRange');
    var minValue = document.getElementById('minValue');
    var maxValue = document.getElementById('maxValue');
    var minInput = document.getElementById('minPriceInput');
    var maxInput = document.getElementById('maxPriceInput');
    
    var minPercentage = (minPrice / 500) * 100;
    var maxPercentage = (maxPrice / 500) * 100;
    
    minThumb.style.left = minPercentage + '%';
    maxThumb.style.left = maxPercentage + '%';
    
    sliderRange.style.left = minPercentage + '%';
    sliderRange.style.right = (100 - maxPercentage) + '%';
    
    minValue.textContent = '$' + minPrice;
    maxValue.textContent = '$' + maxPrice;
    
    minInput.value = minPrice;
    maxInput.value = maxPrice;
}

// Toggle filtros avanzados
function toggleAdvancedFilters() {
    var panel = document.getElementById('advancedFiltersPanel');
    var overlay = document.querySelector('.filters-overlay');
    
    panel.classList.toggle('open');
    overlay.classList.toggle('show');
    
    // Prevenir scroll del body
    if (panel.classList.contains('open')) {
        document.body.style.overflow = 'hidden';
    } else {
        document.body.style.overflow = '';
    }
}

// Abrir filtros avanzados
function openAdvancedFilters() {
    var panel = document.getElementById('advancedFiltersPanel');
    var overlay = document.querySelector('.filters-overlay');
    
    panel.classList.add('open');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
}

// Cerrar filtros avanzados
function closeAdvancedFilters() {
    var panel = document.getElementById('advancedFiltersPanel');
    var overlay = document.querySelector('.filters-overlay');
    
    panel.classList.remove('open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
}

// Aplicar filtros avanzados
function applyAdvancedFilters() {
    var params = new URLSearchParams(window.location.search);
    
    // Precio
    params.set('precio_min', minPrice);
    params.set('precio_max', maxPrice);
    
    // Notas olfativas
    var notas = [];
    document.querySelectorAll('input[name="notas"]:checked').forEach(function(checkbox) {
        notas.push(checkbox.value);
    });
    if (notas.length > 0) {
        params.set('notas', notas.join(','));
    }
    
    // Intensidad
    var intensidad = document.querySelector('input[name="intensidad"]:checked');
    if (intensidad) {
        params.set('intensidad', intensidad.value);
    }
    
    // Ocasión
    var ocasiones = [];
    document.querySelectorAll('.occasion-pill.active').forEach(function(pill) {
        ocasiones.push(pill.dataset.occasion);
    });
    if (ocasiones.length > 0) {
        params.set('ocasion', ocasiones.join(','));
    }
    
    // Redirigir con nuevos filtros
    window.location.href = '/catalogo/?' + params.toString();
}

// Limpiar filtros avanzados
function clearAdvancedFilters() {
    // Resetear slider
    minPrice = 0;
    maxPrice = 500;
    updateSlider();
    
    // Limpiar checkboxes
    document.querySelectorAll('input[type="checkbox"]:checked').forEach(function(checkbox) {
        checkbox.checked = false;
    });
    
    // Limpiar radio buttons
    document.querySelectorAll('input[type="radio"]:checked').forEach(function(radio) {
        radio.checked = false;
    });
    
    // Limpiar pills
    document.querySelectorAll('.occasion-pill.active').forEach(function(pill) {
        pill.classList.remove('active');
    });
}

// Inicializar pills de ocasión
function initOccasionPills() {
    document.querySelectorAll('.occasion-pill').forEach(function(pill) {
        pill.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    });
}

// Cargar filtros desde URL
function loadFiltersFromURL() {
    var params = new URLSearchParams(window.location.search);
    
    // Precio
    var precioMin = params.get('precio_min');
    var precioMax = params.get('precio_max');
    
    if (precioMin) {
        minPrice = parseInt(precioMin);
    }
    if (precioMax) {
        maxPrice = parseInt(precioMax);
    }
    updateSlider();
    
    // Notas
    var notas = params.get('notas');
    if (notas) {
        var notasArray = notas.split(',');
        notasArray.forEach(function(nota) {
            var checkbox = document.querySelector('input[name="notas"][value="' + nota + '"]');
            if (checkbox) {
                checkbox.checked = true;
            }
        });
    }
    
    // Intensidad
    var intensidad = params.get('intensidad');
    if (intensidad) {
        var radio = document.querySelector('input[name="intensidad"][value="' + intensidad + '"]');
        if (radio) {
            radio.checked = true;
        }
    }
    
    // Ocasión
    var ocasion = params.get('ocasion');
    if (ocasion) {
        var ocasionesArray = ocasion.split(',');
        ocasionesArray.forEach(function(oc) {
            var pill = document.querySelector('.occasion-pill[data-occasion="' + oc + '"]');
            if (pill) {
                pill.classList.add('active');
            }
        });
    }
}

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    initPriceSlider();
    initOccasionPills();
    loadFiltersFromURL();
    
    // Cerrar con ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            var panel = document.getElementById('advancedFiltersPanel');
            if (panel.classList.contains('open')) {
                closeAdvancedFilters();
            }
        }
    });
    
    // Cerrar al hacer click en overlay
    var overlay = document.querySelector('.filters-overlay');
    if (overlay) {
        overlay.addEventListener('click', closeAdvancedFilters);
    }
});

// Función global para abrir filtros (desde el catálogo)
window.openAdvancedFilters = openAdvancedFilters;
