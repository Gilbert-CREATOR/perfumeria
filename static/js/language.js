(function() {
  'use strict';

  var translations = {
    'HOME': 'INICIO',
    'Home Page': 'Página principal',
    'CATALOG': 'CATÁLOGO',
    'Catalogue': 'Catálogo',
    'BLOG': 'BLOG',
    'CONTACT': 'CONTACTO',
    'CONTACTS': 'CONTACTOS',
    'ACCOUNT': 'CUENTA',
    'CART': 'CARRITO',
    'ADMIN': 'ADMINISTRACIÓN',
    'FOLLOW': 'SÍGUENOS',
    'INFORMATION': 'INFORMACIÓN',
    'NEWSLETTER': 'BOLETÍN',
    'DELIVERY & RETURNS': 'ENVÍOS Y DEVOLUCIONES',
    'TERMS & CONDITION': 'TÉRMINOS Y CONDICIONES',
    'EMAIL ADDRESS': 'CORREO ELECTRÓNICO',
    'SUBSCRIBE': 'SUSCRIBIRME',
    'DISCOVER': 'DESCUBRIR',
    'NEW COLLECTION': 'NUEVA COLECCIÓN',
    'ABOUT': 'NOSOTROS',
    'VIEW ALL PRODUCTS': 'VER TODOS LOS PRODUCTOS',
    'ALL': 'TODOS',
    'WINTER': 'INVIERNO',
    'SPRING': 'PRIMAVERA',
    'SUMMER': 'VERANO',
    'AUTUMN': 'OTOÑO',
    'DAY': 'DÍA',
    'NIGHT': 'NOCHE',
    'Winter': 'Invierno',
    'Spring': 'Primavera',
    'Summer': 'Verano',
    'Autumn': 'Otoño',
    'Day': 'Día',
    'Night': 'Noche',
    'FILTERS +': 'FILTROS +',
    'SORT BY +': 'ORDENAR +',
    'BRAND': 'MARCA',
    'ALL BRANDS': 'TODAS LAS MARCAS',
    'MIN PRICE': 'PRECIO MÍNIMO',
    'MAX PRICE': 'PRECIO MÁXIMO',
    'APPLY': 'APLICAR',
    'CLEAR': 'LIMPIAR',
    'NAME': 'NOMBRE',
    'PRICE: LOW TO HIGH': 'PRECIO: MENOR A MAYOR',
    'PRICE: HIGH TO LOW': 'PRECIO: MAYOR A MENOR',
    'POPULARITY': 'POPULARIDAD',
    'PREVIOUS': 'ANTERIOR',
    'NEXT': 'SIGUIENTE',
    'LOGIN': 'INICIAR SESIÓN',
    'Welcome Back': 'Bienvenido de nuevo',
    'USERNAME': 'USUARIO',
    'PASSWORD': 'CONTRASEÑA',
    'EMAIL': 'CORREO ELECTRÓNICO',
    'REGISTER': 'REGISTRARSE',
    'Create Account': 'Crear cuenta',
    'CONFIRM PASSWORD': 'CONFIRMAR CONTRASEÑA',
    'USERNAME OR EMAIL': 'USUARIO O CORREO ELECTRÓNICO',
    'Enter your username or email': 'Ingresa tu usuario o correo',
    'Choose a username': 'Elige un nombre de usuario',
    'Enter your email': 'Ingresa tu correo electrónico',
    'Enter your first name': 'Ingresa tu nombre',
    'Enter your last name': 'Ingresa tus apellidos',
    'Create a password': 'Crea una contraseña',
    'Confirm your password': 'Confirma tu contraseña',
    'By creating an account, you agree to our Privacy Policy and Terms of Service.': 'Al crear una cuenta, aceptas nuestra Política de privacidad y los Términos de servicio.',
    'Remember me': 'Recordarme',
    "Don't have an account?": '¿No tienes una cuenta?',
    'Create an account': 'Crear una cuenta',
    'Forgot your password?': '¿Olvidaste tu contraseña?',
    'PROFILE': 'PERFIL',
    'My Profile': 'Mi perfil',
    'FIRST NAME': 'NOMBRE',
    'LAST NAME': 'APELLIDOS',
    'PHONE': 'TELÉFONO',
    'UPDATE PROFILE': 'ACTUALIZAR PERFIL',
    'Order History': 'Historial de pedidos',
    'My Favorites': 'Mis favoritos',
    'No favorites yet': 'Todavía no tienes favoritos',
    'No orders yet': 'Todavía no tienes pedidos',
    'LOGOUT': 'CERRAR SESIÓN',
    'REMOVE': 'ELIMINAR',
    'QUANTITY:': 'CANTIDAD:',
    'Order Summary': 'Resumen del pedido',
    'Subtotal': 'Subtotal',
    'Shipping': 'Envío',
    'FREE': 'GRATIS',
    'Total': 'Total',
    'PROCEED TO CHECKOUT': 'CONTINUAR AL PAGO',
    'Continue Shopping': 'SEGUIR COMPRANDO',
    'Your cart is empty': 'Tu carrito está vacío',
    'Add some products to get started': 'Agrega productos para comenzar',
    'You might also like': 'TAMBIÉN PODRÍA GUSTARTE',
    'YOU MIGHT ALSO LIKE': 'TAMBIÉN PODRÍA GUSTARTE',
    'ADD TO CART': 'AGREGAR AL CARRITO',
    'ADD TO FAVORITES': 'AGREGAR A FAVORITOS',
    'REMOVE FROM FAVORITES': 'QUITAR DE FAVORITOS',
    'REVIEWS': 'RESEÑAS',
    'REAL EXPERIENCES': 'EXPERIENCIAS REALES',
    'RATING': 'PUNTUACIÓN',
    'YOUR EXPERIENCE': 'TU EXPERIENCIA',
    'SEASONS': 'TEMPORADAS',
    'Sold out': 'Agotado',
    'PERFUME': 'PERFUME',
    'EMAIL SENT': 'CORREO ENVIADO',
    'BACK TO LOGIN': 'VOLVER A INICIAR SESIÓN',
    'SEND INSTRUCTIONS': 'ENVIAR INSTRUCCIONES',
    'SAVE PASSWORD': 'GUARDAR CONTRASEÑA',
    'REQUEST ANOTHER LINK': 'SOLICITAR OTRO ENLACE',
    'DELETE MY ACCOUNT': 'ELIMINAR MI CUENTA',
    'LOGGING OUT': 'SALIENDO',
    'Home Page / Cart': 'Página principal / Carrito',
    'Home Page / Login': 'Página principal / Iniciar sesión',
    'Home Page / Register': 'Página principal / Registro',
    'Home Page / Profile': 'Página principal / Perfil',
    'Home Page / Contact': 'Página principal / Contacto',
    'Home Page / About': 'Página principal / Nosotros',
    'Get in Touch': 'Ponte en contacto',
    'SUBJECT *': 'ASUNTO *',
    'MESSAGE *': 'MENSAJE *',
    'Select a subject': 'Selecciona un asunto',
    'General inquiry': 'Consulta general',
    'About my order': 'Sobre mi pedido',
    'Product information': 'Información del producto',
    'Return or exchange': 'Devolución o cambio',
    'Technical issue': 'Problema técnico',
    'Collaboration proposal': 'Propuesta de colaboración',
    'Other': 'Otro',
    'Contact Information': 'Información de contacto',
    'Address': 'Dirección',
    'Phone': 'Teléfono',
    'Email': 'Correo electrónico',
    'Business Hours': 'Horario comercial',
    'Monday - Friday': 'Lunes - Viernes',
    'Saturday': 'Sábado',
    'Sunday': 'Domingo',
    'Closed': 'Cerrado',
    'Follow Us': 'Síguenos',
    'Find Us': 'Encuéntranos',
    'Our Philosophy': 'Nuestra filosofía',
    'Our Craft': 'Nuestro trabajo',
    'Our Values': 'Nuestros valores',
    'Simplicity': 'Simplicidad',
    'Quality': 'Calidad',
    'Innovation': 'Innovación',
    'Visit Our Studio': 'Visita nuestro estudio',
    'Location': 'Ubicación',
    'Hours': 'Horario',
    'Frequently Asked Questions': 'Preguntas frecuentes',
    'Still have questions?': '¿Todavía tienes preguntas?',
    'ACCOUNT ACCESS': 'ACCESO A TU CUENTA',
    'RESET YOUR PASSWORD': 'RECUPERA TU CONTRASEÑA',
    'Enter the email associated with your account. We will send you a secure link to create a new password.': 'Escribe el correo asociado a tu cuenta. Te enviaremos un enlace seguro para crear una contraseña nueva.',
    'Email address': 'Correo electrónico',
    '← BACK TO LOGIN': '← VOLVER A INICIAR SESIÓN',
    '01 / SECURITY': '01 / SEGURIDAD',
    'The link will only work for a limited time. If you do not see the message, check your spam folder.': 'El enlace solo funcionará durante un tiempo limitado. Si no ves el mensaje, revisa la carpeta de correo no deseado.',
    'There are no reviews yet.': 'Todavía no hay reseñas.',
    'Product temporarily out of stock': 'Producto temporalmente agotado'
  };

  var reverseTranslations = {};
  Object.keys(translations).forEach(function(key) {
    reverseTranslations[translations[key]] = key;
  });

  function savedLanguage() {
    try {
      return window.localStorage.getItem('darcy-language');
    } catch (error) {
      return null;
    }
  }

  function rememberLanguage(language) {
    try {
      window.localStorage.setItem('darcy-language', language);
    } catch (error) {
      // El selector sigue funcionando aunque el navegador bloquee el almacenamiento.
    }
  }

  function preferredLanguage() {
    var saved = savedLanguage();
    if (saved === 'es' || saved === 'en') return saved;
    return (window.navigator.language || '').toLowerCase().indexOf('es') === 0 ? 'es' : 'en';
  }

  function translateValue(value, language) {
    if (!value) return value;
    var leading = value.match(/^\s*/)[0];
    var trailing = value.match(/\s*$/)[0];
    var text = value.trim();
    var canonical = Object.prototype.hasOwnProperty.call(translations, text)
      ? text
      : reverseTranslations[text];
    if (!canonical) return value;
    var result = language === 'es' ? translations[canonical] : canonical;
    return leading + result + trailing;
  }

  function translateTextNode(node, language) {
    var current = node.nodeValue;
    var trimmed = current.trim();
    var canonical = Object.prototype.hasOwnProperty.call(translations, trimmed)
      ? trimmed
      : reverseTranslations[trimmed];
    if (!canonical) return;

    if (!node.__darcyCanonical || node.__darcyCanonical !== canonical) {
      node.__darcyCanonical = canonical;
      node.__darcyLeadingSpace = current.match(/^\s*/)[0];
      node.__darcyTrailingSpace = current.match(/\s*$/)[0];
    }
    var translated = language === 'es' ? translations[node.__darcyCanonical] : node.__darcyCanonical;
    var desired = node.__darcyLeadingSpace + translated + node.__darcyTrailingSpace;
    if (node.nodeValue !== desired) node.nodeValue = desired;
  }

  function translateElement(element, language) {
    if (element.closest('[data-no-translate]') ||
        element.matches('[data-language-toggle], .product-title, .product-card h2, .product-card h3')) return;

    if (element.hasAttribute('data-i18n')) {
      var key = element.getAttribute('data-i18n');
      var desiredText = language === 'es' ? (translations[key] || key) : key;
      if (element.textContent !== desiredText) element.textContent = desiredText;
    } else {
      Array.prototype.forEach.call(element.childNodes, function(node) {
        if (node.nodeType === Node.TEXT_NODE) translateTextNode(node, language);
      });
    }

    ['placeholder'].forEach(function(attribute) {
      if (!element.hasAttribute(attribute)) return;
      var storageKey = 'darcyOriginal' + attribute.replace('-', '');
      if (!element.dataset[storageKey]) element.dataset[storageKey] = element.getAttribute(attribute);
      var desiredAttribute = translateValue(element.dataset[storageKey], language);
      if (element.getAttribute(attribute) !== desiredAttribute) element.setAttribute(attribute, desiredAttribute);
    });
  }

  function updateToggle(language) {
    document.querySelectorAll('[data-language-toggle]').forEach(function(button) {
      var target = language === 'es' ? 'en' : 'es';
      var label = target.toUpperCase();
      var ariaLabel = language === 'es' ? 'Cambiar idioma a inglés' : 'Change language to Spanish';
      var title = language === 'es' ? 'Cambiar a inglés' : 'Change to Spanish';
      if (button.textContent !== label) button.textContent = label;
      if (button.getAttribute('aria-label') !== ariaLabel) button.setAttribute('aria-label', ariaLabel);
      if (button.getAttribute('title') !== title) button.setAttribute('title', title);
    });
  }

  function applyLanguage(language) {
    document.documentElement.lang = language;
    document.querySelectorAll('body *').forEach(function(element) {
      translateElement(element, language);
    });
    updateToggle(language);
    rememberLanguage(language);
    document.dispatchEvent(new CustomEvent('darcy:languagechange', {detail: {language: language}}));
  }

  document.addEventListener('DOMContentLoaded', function() {
    var language = preferredLanguage();
    applyLanguage(language);

    document.addEventListener('click', function(event) {
      var button = event.target.closest('[data-language-toggle]');
      if (!button) return;
      language = document.documentElement.lang === 'es' ? 'en' : 'es';
      applyLanguage(language);
    });

    var updateScheduled = false;
    new MutationObserver(function() {
      if (updateScheduled) return;
      updateScheduled = true;
      window.requestAnimationFrame(function() {
        updateScheduled = false;
        document.querySelectorAll('body *').forEach(function(element) {
          translateElement(element, document.documentElement.lang || language);
        });
        updateToggle(document.documentElement.lang || language);
      });
    }).observe(document.body, {childList: true, subtree: true, characterData: true});
  });
}());
