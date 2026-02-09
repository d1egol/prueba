// ==================== CONFIGURACIÓN EDITABLE ====================
const CONFIG = {
    whatsapp: '+56912345678', // CAMBIAR por tu número real
    emailPedidos: 'pedidos@tutienda.cl', // CAMBIAR por tu email
    costoEnvio: {
        starken: 3990,
        chilexpress: 4990,
        retiro: 0
    }
};

// ==================== CATÁLOGO DE PRODUCTOS ====================
// PARA AGREGAR NUEVOS DISEÑOS: copia un objeto y modifica id, nombre, descripción, precio, imagen y tags
const PRODUCTOS = [
    {
        id: 'POL-001',
        nombre: 'Monkey Vibes',
        descripcion: 'Chimpancé cool con estilo tropical y actitud relajada',
        tags: ['animal', 'tropical', 'urbano', 'humor', 'verano'],
        precio: 18990,
        imagen: 'assets/diseno-01-monkey-vibes.png',
        variantes: {
            tallas: ['S', 'M', 'L', 'XL'],
            colores: ['Negro', 'Blanco', 'Gris']
        }
    },
    {
        id: 'POL-002',
        nombre: 'Boss Dog',
        descripcion: 'Labrador gangster con estilo urbano y cadena de oro',
        tags: ['animal', 'urbano', 'humor', 'perro', 'swag'],
        precio: 18990,
        imagen: 'assets/diseno-02-boss-dog.png',
        variantes: {
            tallas: ['S', 'M', 'L', 'XL'],
            colores: ['Negro', 'Blanco', 'Gris']
        }
    },
    {
        id: 'POL-003',
        nombre: 'Chill Cat',
        descripcion: 'Gato meditativo con hoodie verde y actitud zen',
        tags: ['animal', 'zen', 'urbano', 'gato', 'relax'],
        precio: 18990,
        imagen: 'assets/diseno-03-chill-cat.png',
        variantes: {
            tallas: ['S', 'M', 'L', 'XL'],
            colores: ['Negro', 'Blanco', 'Gris']
        }
    },
    {
        id: 'POL-004',
        nombre: 'Tribal Tiki',
        descripcion: 'Arte tribal polinésico con máscaras y símbolos ancestrales',
        tags: ['tribal', 'arte', 'cultural', 'simbólico', 'étnico'],
        precio: 19990,
        imagen: 'assets/diseno-04-tribal-tiki.png',
        variantes: {
            tallas: ['S', 'M', 'L', 'XL'],
            colores: ['Negro', 'Blanco', 'Gris']
        }
    },
    {
        id: 'POL-005',
        nombre: 'Psycho Goat',
        descripcion: 'Cabra psicodélica con cuernos y ondas hipnóticas rojas',
        tags: ['psicodélico', 'animal', 'arte', 'rock', 'alternativo'],
        precio: 19990,
        imagen: 'assets/diseno-05-psycho-goat.png',
        variantes: {
            tallas: ['S', 'M', 'L', 'XL'],
            colores: ['Negro', 'Blanco', 'Gris']
        }
    },
    {
        id: 'POL-006',
        nombre: 'Sheep Squad',
        descripcion: 'Rebaño de ovejas con lentes oscuros en blanco y negro',
        tags: ['humor', 'animal', 'vintage', 'surrealista', 'fotografía'],
        precio: 18990,
        imagen: 'assets/diseno-06-sheep-squad.png',
        variantes: {
            tallas: ['S', 'M', 'L', 'XL'],
            colores: ['Negro', 'Blanco', 'Gris']
        }
    }
];

// ==================== ESTADO GLOBAL ====================
let carrito = JSON.parse(localStorage.getItem('carrito')) || [];
let productoActual = null;

// ==================== ELEMENTOS DEL DOM ====================
const elements = {
    catalogGrid: document.getElementById('catalogGrid'),
    cartBtn: document.getElementById('cartBtn'),
    cartCount: document.getElementById('cartCount'),
    cartDrawer: document.getElementById('cartDrawer'),
    cartClose: document.getElementById('cartClose'),
    cartItems: document.getElementById('cartItems'),
    cartSubtotal: document.getElementById('cartSubtotal'),
    cartShipping: document.getElementById('cartShipping'),
    cartTotal: document.getElementById('cartTotal'),
    overlay: document.getElementById('overlay'),
    productModal: document.getElementById('productModal'),
    modalClose: document.getElementById('modalClose'),
    addToCartBtn: document.getElementById('addToCartBtn'),
    checkoutBtn: document.getElementById('checkoutBtn'),
    checkoutSection: document.getElementById('checkoutSection'),
    checkoutForm: document.getElementById('checkoutForm'),
    ctaBtn: document.getElementById('ctaBtn'),
    searchInput: document.getElementById('searchInput'),
    filterTalla: document.getElementById('filterTalla'),
    filterColor: document.getElementById('filterColor'),
    filterPrecio: document.getElementById('filterPrecio'),
    filterTag: document.getElementById('filterTag')
};

// ==================== FUNCIONES UTILIDAD ====================
function formatCLP(amount) {
    return '$' + amount.toLocaleString('es-CL');
}

function guardarCarrito() {
    localStorage.setItem('carrito', JSON.stringify(carrito));
}

function actualizarContadorCarrito() {
    const totalItems = carrito.reduce((sum, item) => sum + item.cantidad, 0);
    elements.cartCount.textContent = totalItems;
}

// ==================== RENDERIZADO DE PRODUCTOS ====================
function renderizarProductos(productos) {
    if (productos === undefined) productos = PRODUCTOS;
    elements.catalogGrid.innerHTML = productos.map(producto => `
        <div class="product-card" data-id="${producto.id}">
            <img src="${producto.imagen}" alt="${producto.nombre}" class="product-image" loading="lazy">
            <div class="product-info">
                <h3 class="product-name">${producto.nombre}</h3>
                <p class="product-description">${producto.descripcion}</p>
                <div class="product-tags">
                    ${producto.tags.slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('')}
                </div>
                <p class="product-price">${formatCLP(producto.precio)}</p>
            </div>
        </div>
    `).join('');

    document.querySelectorAll('.product-card').forEach(card => {
        card.addEventListener('click', () => {
            abrirModal(card.dataset.id);
        });
    });
}

// ==================== MODAL DE PRODUCTO ====================
function abrirModal(id) {
    productoActual = PRODUCTOS.find(p => p.id === id);
    if (!productoActual) return;

    document.getElementById('modalImage').src = productoActual.imagen;
    document.getElementById('modalImage').alt = productoActual.nombre;
    document.getElementById('modalTitle').textContent = productoActual.nombre;
    document.getElementById('modalDescription').textContent = productoActual.descripcion;
    document.getElementById('modalPrice').textContent = formatCLP(productoActual.precio);
    document.getElementById('modalTags').innerHTML = productoActual.tags.map(tag =>
        `<span class="tag">${tag}</span>`
    ).join('');

    elements.productModal.classList.add('active');
    elements.overlay.classList.add('active');
}

function cerrarModal() {
    elements.productModal.classList.remove('active');
    elements.overlay.classList.remove('active');
    productoActual = null;
}

// ==================== GESTIÓN DEL CARRITO ====================
function agregarAlCarrito() {
    if (!productoActual) return;

    const talla = document.getElementById('modalTalla').value;
    const color = document.getElementById('modalColor').value;
    const cantidad = parseInt(document.getElementById('modalCantidad').value);

    const itemExistente = carrito.find(item =>
        item.id === productoActual.id && item.talla === talla && item.color === color
    );

    if (itemExistente) {
        itemExistente.cantidad += cantidad;
    } else {
        carrito.push({
            id: productoActual.id,
            nombre: productoActual.nombre,
            precio: productoActual.precio,
            imagen: productoActual.imagen,
            talla,
            color,
            cantidad
        });
    }

    guardarCarrito();
    actualizarCarrito();
    cerrarModal();
    abrirCarrito();
}

function eliminarDelCarrito(index) {
    carrito.splice(index, 1);
    guardarCarrito();
    actualizarCarrito();
}

function actualizarCarrito() {
    actualizarContadorCarrito();

    const subtotal = carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    const envio = subtotal > 0 ? 3990 : 0;
    const total = subtotal + envio;

    elements.cartSubtotal.textContent = formatCLP(subtotal);
    elements.cartShipping.textContent = formatCLP(envio);
    elements.cartTotal.textContent = formatCLP(total);

    elements.cartItems.innerHTML = carrito.length === 0
        ? '<p style="text-align:center; padding:2rem; color:#636E72;">Tu carrito está vacío</p>'
        : carrito.map((item, index) => `
            <div class="cart-item">
                <img src="${item.imagen}" alt="${item.nombre}" class="cart-item-image">
                <div class="cart-item-info">
                    <h4>${item.nombre}</h4>
                    <p>${item.talla} - ${item.color} - x${item.cantidad}</p>
                    <p style="font-weight:700; color:#FF6B6B;">${formatCLP(item.precio * item.cantidad)}</p>
                </div>
                <button class="cart-item-remove" onclick="eliminarDelCarrito(${index})">X</button>
            </div>
        `).join('');
}

function abrirCarrito() {
    elements.cartDrawer.classList.add('active');
    elements.overlay.classList.add('active');
}

function cerrarCarrito() {
    elements.cartDrawer.classList.remove('active');
    elements.overlay.classList.remove('active');
}

// ==================== CHECKOUT ====================
function irACheckout() {
    if (carrito.length === 0) {
        alert('Tu carrito está vacío');
        return;
    }

    cerrarCarrito();
    elements.checkoutSection.classList.remove('hidden');
    window.scrollTo({ top: 0, behavior: 'smooth' });

    const subtotal = carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    const envio = 3990;

    document.getElementById('checkoutSubtotal').textContent = formatCLP(subtotal);
    document.getElementById('checkoutShipping').textContent = formatCLP(envio);
    document.getElementById('checkoutTotal').textContent = formatCLP(subtotal + envio);

    document.getElementById('checkoutItems').innerHTML = carrito.map(item => `
        <div class="checkout-item">
            <span>${item.nombre} (${item.talla}, ${item.color}) x${item.cantidad}</span>
            <span>${formatCLP(item.precio * item.cantidad)}</span>
        </div>
    `).join('');
}

function finalizarPedido(e) {
    e.preventDefault();

    const datos = {
        nombre: document.getElementById('nombre').value,
        email: document.getElementById('email').value,
        telefono: document.getElementById('telefono').value,
        direccion: document.getElementById('direccion').value,
        comuna: document.getElementById('comuna').value,
        envio: document.getElementById('envio').value
    };

    const subtotal = carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    const costoEnvio = CONFIG.costoEnvio[datos.envio];
    const total = subtotal + costoEnvio;

    // MENSAJE WHATSAPP
    const mensajeWA = [
        '*NUEVO PEDIDO - Poleras by Diego*',
        '',
        '*Cliente:* ' + datos.nombre,
        '*Email:* ' + datos.email,
        '*Teléfono:* ' + datos.telefono,
        '*Dirección:* ' + datos.direccion + ', ' + datos.comuna,
        '*Envío:* ' + datos.envio,
        '',
        '*PRODUCTOS:*',
        ...carrito.map(item =>
            '- ' + item.nombre + ' (' + item.talla + ', ' + item.color + ') x' + item.cantidad + ' - ' + formatCLP(item.precio * item.cantidad)
        ),
        '',
        '*TOTAL:* ' + formatCLP(total) + ' (Subtotal: ' + formatCLP(subtotal) + ' + Envío: ' + formatCLP(costoEnvio) + ')'
    ].join('\n');

    const urlWA = 'https://wa.me/' + CONFIG.whatsapp.replace('+', '') + '?text=' + encodeURIComponent(mensajeWA);

    // EMAIL
    const asuntoEmail = 'Pedido ' + datos.nombre + ' - Poleras by Diego';
    const cuerpoEmail = [
        'NUEVO PEDIDO',
        '',
        'Cliente: ' + datos.nombre,
        'Email: ' + datos.email,
        'Teléfono: ' + datos.telefono,
        'Dirección: ' + datos.direccion + ', ' + datos.comuna,
        'Método envío: ' + datos.envio,
        '',
        'PRODUCTOS:',
        ...carrito.map(item =>
            item.nombre + ' (' + item.talla + ', ' + item.color + ') x' + item.cantidad + ' - ' + formatCLP(item.precio * item.cantidad)
        ),
        '',
        'TOTAL: ' + formatCLP(total)
    ].join('\n');

    const urlEmail = 'mailto:' + CONFIG.emailPedidos + '?subject=' + encodeURIComponent(asuntoEmail) + '&body=' + encodeURIComponent(cuerpoEmail);

    // Mostrar opciones al usuario
    var confirmacion = confirm(
        '¡Pedido listo!\n\n' +
        'Presiona OK para enviar por WhatsApp\n' +
        'Presiona Cancelar para enviar por Email'
    );

    if (confirmacion) {
        window.open(urlWA, '_blank');
    } else {
        window.location.href = urlEmail;
    }

    // Limpiar carrito
    carrito = [];
    guardarCarrito();
    actualizarCarrito();
    elements.checkoutSection.classList.add('hidden');
    alert('¡Gracias por tu pedido! Te contactaremos pronto.');
}

// ==================== FILTROS Y BÚSQUEDA ====================
function aplicarFiltros() {
    const busqueda = elements.searchInput.value.toLowerCase();
    const talla = elements.filterTalla.value;
    const color = elements.filterColor.value;
    const precioMax = parseInt(elements.filterPrecio.value) || Infinity;
    const tag = elements.filterTag.value;

    const productosFiltrados = PRODUCTOS.filter(producto => {
        const coincideBusqueda = producto.nombre.toLowerCase().includes(busqueda) ||
                                  producto.descripcion.toLowerCase().includes(busqueda);
        const coincideTalla = !talla || producto.variantes.tallas.includes(talla);
        const coincideColor = !color || producto.variantes.colores.includes(color);
        const coincidePrecio = producto.precio <= precioMax;
        const coincideTag = !tag || producto.tags.includes(tag);

        return coincideBusqueda && coincideTalla && coincideColor && coincidePrecio && coincideTag;
    });

    renderizarProductos(productosFiltrados);
}

// ==================== EVENT LISTENERS ====================
elements.cartBtn.addEventListener('click', abrirCarrito);
elements.cartClose.addEventListener('click', cerrarCarrito);
elements.modalClose.addEventListener('click', cerrarModal);
elements.addToCartBtn.addEventListener('click', agregarAlCarrito);
elements.checkoutBtn.addEventListener('click', irACheckout);
elements.checkoutForm.addEventListener('submit', finalizarPedido);
elements.ctaBtn.addEventListener('click', () => {
    document.getElementById('catalog').scrollIntoView({ behavior: 'smooth' });
});

elements.overlay.addEventListener('click', () => {
    cerrarModal();
    cerrarCarrito();
});

elements.searchInput.addEventListener('input', aplicarFiltros);
elements.filterTalla.addEventListener('change', aplicarFiltros);
elements.filterColor.addEventListener('change', aplicarFiltros);
elements.filterPrecio.addEventListener('input', aplicarFiltros);
elements.filterTag.addEventListener('change', aplicarFiltros);

// Actualizar costo de envío en tiempo real
document.getElementById('envio').addEventListener('change', (e) => {
    const metodo = e.target.value;
    const costo = CONFIG.costoEnvio[metodo];
    document.getElementById('checkoutShipping').textContent = formatCLP(costo);

    const subtotal = carrito.reduce((sum, item) => sum + (item.precio * item.cantidad), 0);
    document.getElementById('checkoutTotal').textContent = formatCLP(subtotal + costo);
});

// ==================== INICIALIZACIÓN ====================
document.addEventListener('DOMContentLoaded', () => {
    renderizarProductos();
    actualizarCarrito();
});
