// Quick Preview JavaScript
var currentProductId = null;
var maxStock = 0;

// Abrir Quick Preview
function openQuickPreview(productId) {
    currentProductId = productId;
    
    // Mostrar modal con animación
    var modal = document.getElementById('quickPreviewModal');
    modal.style.display = 'flex';
    
    // Forzar reflow para animación
    modal.offsetHeight;
    
    modal.classList.add('show');
    
    // Cargar datos del producto
    loadProductData(productId);
    
    // Prevenir scroll del body
    document.body.style.overflow = 'hidden';
}

// Cerrar Quick Preview
function closeQuickPreview() {
    var modal = document.getElementById('quickPreviewModal');
    modal.classList.remove('show');
    
    setTimeout(function() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    }, 300);
}

// Cargar datos del producto via AJAX
function loadProductData(productId) {
    // Mostrar loading
    showLoadingState();
    
    fetch('/productos/api/quick-preview/' + productId + '/')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                populateModal(data.product);
                setupModalActions(data.product);
            } else {
                showError('No se pudo cargar el producto');
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
            showError('Error de conexión');
        });
}

// Llenar modal con datos del producto
function populateModal(product) {
    // Información básica
    document.getElementById('modalTitle').textContent = product.nombre;
    document.getElementById('modalBrand').textContent = product.marca;
    document.getElementById('modalPrice').textContent = '$' + new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }).format(parseFloat(product.precio));
    document.getElementById('modalSize').textContent = product.tamano_ml;
    document.getElementById('modalDescription').textContent = product.descripcion;
    document.getElementById('modalType').textContent = product.tipo_display;
    document.getElementById('modalSeason').textContent = product.temporada_display || 'Todas';
    document.getElementById('modalCode').textContent = 'PRD-' + String(product.id).padStart(6, '0');
    
    // Rating
    var starsHtml = '';
    var rating = parseFloat(product.rating_promedio) || 0;
    for (var i = 1; i <= 5; i++) {
        starsHtml += i <= rating ? '⭐' : '☆';
    }
    document.getElementById('modalStars').innerHTML = starsHtml;
    document.getElementById('modalRating').textContent = 
        (rating ? rating.toFixed(1) + ' (' + product.total_resenas + ' reseñas)' : 'Sin reseñas');
    
    // Stock
    maxStock = product.stock || 0;
    var stockElement = document.getElementById('modalStock');
    var quantityInput = document.getElementById('modalQuantity');
    var addToCartBtn = document.getElementById('modalAddToCart');
    
    quantityInput.max = maxStock;
    quantityInput.value = 1;
    
    if (maxStock > 0) {
        if (maxStock < 5) {
            stockElement.className = 'modal-stock low-stock';
            stockElement.textContent = '¡Últimas ' + maxStock + ' unidades!';
        } else {
            stockElement.className = 'modal-stock in-stock';
            stockElement.textContent = maxStock + ' unidades disponibles';
        }
        addToCartBtn.disabled = false;
        addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> Agregar';
    } else {
        stockElement.className = 'modal-stock out-of-stock';
        stockElement.textContent = 'Producto agotado';
        addToCartBtn.disabled = true;
        addToCartBtn.innerHTML = '<i class="fas fa-times"></i> Agotado';
    }
    
    // Imagen
    var modalImage = document.getElementById('modalImage');
    var placeholder = document.getElementById('modalImagePlaceholder');
    
    if (product.imagen) {
        modalImage.src = product.imagen;
        modalImage.alt = product.nombre;
        modalImage.style.display = 'block';
        placeholder.style.display = 'none';
    } else {
        modalImage.style.display = 'none';
        placeholder.style.display = 'flex';
    }
    
    // Botón de detalles
    document.getElementById('modalViewDetails').onclick = function() {
        window.location.href = '/productos/' + product.id + '/';
    };
}

// Configurar acciones del modal
function setupModalActions(product) {
    var decreaseBtn = document.getElementById('modalDecrease');
    var increaseBtn = document.getElementById('modalIncrease');
    var quantityInput = document.getElementById('modalQuantity');
    var addToCartBtn = document.getElementById('modalAddToCart');
    
    // Control de cantidad
    decreaseBtn.onclick = function() {
        var currentValue = parseInt(quantityInput.value);
        if (currentValue > 1) {
            quantityInput.value = currentValue - 1;
        }
    };
    
    increaseBtn.onclick = function() {
        var currentValue = parseInt(quantityInput.value);
        if (maxStock > 0 && currentValue < maxStock) {
            quantityInput.value = currentValue + 1;
        }
    };
    
    quantityInput.onchange = function() {
        var value = parseInt(this.value);
        if (isNaN(value) || value < 1) {
            this.value = 1;
        } else if (maxStock > 0 && value > maxStock) {
            this.value = maxStock;
        }
    };
    
    // Agregar al carrito
    addToCartBtn.onclick = function() {
        if (maxStock === 0) return;
        
        var quantity = quantityInput.value;
        
        this.disabled = true;
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Agregando...';
        
        addToCartFromModal(currentProductId, quantity);
    };
}

// Agregar al carrito desde el modal
function addToCartFromModal(productId, quantity) {
    fetch('/carrito/agregar/' + productId + '/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            cantidad: quantity
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        var addToCartBtn = document.getElementById('modalAddToCart');
        
        if (data.success) {
            addToCartBtn.innerHTML = '<i class="fas fa-check"></i> ¡Agregado!';
            addToCartBtn.style.background = '#28a745';
            
            updateCartCount();
            showNotification(data.message || 'Producto agregado al carrito', 'success');
            
            setTimeout(function() {
                addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> Agregar';
                addToCartBtn.style.background = '';
                addToCartBtn.disabled = false;
            }, 2000);
        } else {
            addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> Agregar';
            addToCartBtn.disabled = false;
            
            if (data.redirect) {
                // Redirigir a login si no está autenticado
                window.location.href = data.redirect;
            } else {
                showNotification(data.error || 'Error al agregar producto', 'error');
            }
        }
    })
    .catch(function(error) {
        var addToCartBtn = document.getElementById('modalAddToCart');
        addToCartBtn.innerHTML = '<i class="fas fa-cart-plus"></i> Agregar';
        addToCartBtn.disabled = false;
        showNotification('Error de conexión', 'error');
    });
}

// Estado de carga
function showLoadingState() {
    document.getElementById('modalTitle').textContent = 'Cargando...';
    document.getElementById('modalBrand').textContent = '';
    document.getElementById('modalPrice').textContent = '';
    document.getElementById('modalDescription').textContent = '';
    document.getElementById('modalStars').innerHTML = '';
    document.getElementById('modalRating').textContent = '';
    document.getElementById('modalStock').textContent = '';
    document.getElementById('modalType').textContent = '';
    document.getElementById('modalSeason').textContent = '';
    document.getElementById('modalCode').textContent = '';
    
    var modalImage = document.getElementById('modalImage');
    var placeholder = document.getElementById('modalImagePlaceholder');
    modalImage.style.display = 'none';
    placeholder.style.display = 'flex';
}

// Mostrar error
function showError(message) {
    var modalBody = document.querySelector('.modal-body');
    modalBody.innerHTML = '<div style="text-align: center; padding: 40px;"><i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i><h3>' + message + '</h3><button onclick="closeQuickPreview()" class="btn btn-primary mt-3">Cerrar</button></div>';
}

// Actualizar contador del carrito
function updateCartCount() {
    fetch('/carrito/api/count/')
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            var cartElements = document.querySelectorAll('.cart-count');
            cartElements.forEach(function(element) {
                element.textContent = data.count || 0;
            });
        });
}

// Notificaciones
function showNotification(message, type) {
    var notification = document.createElement('div');
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: ' + (type === 'success' ? '#28a745' : '#dc3545') + '; color: white; padding: 16px 24px; border-radius: 8px; font-size: 0.875rem; z-index: 10000; opacity: 0; transform: translateY(-20px); transition: all 0.3s ease;';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(function() {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 100);
    
    setTimeout(function() {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        setTimeout(function() {
            notification.remove();
        }, 300);
    }, 3000);
}

// CSRF Token
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Cerrar con ESC
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        var modal = document.getElementById('quickPreviewModal');
        if (modal.style.display === 'flex') {
            closeQuickPreview();
        }
    }
});

// Cerrar al hacer click fuera
document.getElementById('quickPreviewModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeQuickPreview();
    }
});
