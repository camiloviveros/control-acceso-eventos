// Main JavaScript File

// Event Detail Page - Ticket Type Selection
document.addEventListener('DOMContentLoaded', function() {
    const ticketTypeSelect = document.getElementById('ticket-type-select');
    const ticketPrice = document.getElementById('ticket-price');
    const ticketQuantity = document.getElementById('id_quantity');
    const totalPrice = document.getElementById('total-price');
    
    if (ticketTypeSelect && ticketPrice && ticketQuantity && totalPrice) {
        // Cuando cambia el tipo de entrada
        ticketTypeSelect.addEventListener('change', function() {
            const selectedOption = ticketTypeSelect.options[ticketTypeSelect.selectedIndex];
            const price = selectedOption.getAttribute('data-price');
            
            ticketPrice.textContent = price;
            updateTotalPrice();
        });
        
        // Cuando cambia la cantidad
        ticketQuantity.addEventListener('change', function() {
            updateTotalPrice();
        });
        
        // Actualizar precio total
        function updateTotalPrice() {
            const price = parseFloat(ticketPrice.textContent);
            const quantity = parseInt(ticketQuantity.value);
            
            if (!isNaN(price) && !isNaN(quantity)) {
                const total = price * quantity;
                totalPrice.textContent = total.toFixed(2);
            }
        }
        
        // Inicializar con los valores actuales
        updateTotalPrice();
    }
});

// Verify Ticket Page - QR Scanner
document.addEventListener('DOMContentLoaded', function() {
    const scannerContainer = document.getElementById('qr-scanner');
    const startScanBtn = document.getElementById('start-scan');
    const stopScanBtn = document.getElementById('stop-scan');
    const scanResult = document.getElementById('scan-result');
    const ticketDetailsContainer = document.getElementById('ticket-details');
    
    if (scannerContainer && startScanBtn && stopScanBtn) {
        let scanner = null;
        
        // Iniciar escaneo
        startScanBtn.addEventListener('click', function() {
            if (scanner) {
                return;
            }
            
            // Comprobar si el navegador soporta la API de MediaDevices
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                scanResult.innerHTML = '<div class="alert alert-danger">Tu navegador no soporta la cámara. Por favor, usa un navegador más moderno o ingresa el código manualmente.</div>';
                return;
            }
            
            // Mostrar elemento de video
            scannerContainer.innerHTML = '<video id="qr-video" class="w-100"></video>';
            const videoElem = document.getElementById('qr-video');
            
            // Solicitar acceso a la cámara
            navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
                .then(function(stream) {
                    videoElem.srcObject = stream;
                    videoElem.setAttribute("playsinline", true);
                    videoElem.play();
                    
                    // Crear un canvas para capturar frames
                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    const scanInterval = 100; // Escanear cada 100ms
                    
                    // Función para escanear un frame
                    function scanFrame() {
                        if (videoElem.readyState === videoElem.HAVE_ENOUGH_DATA) {
                            canvas.height = videoElem.videoHeight;
                            canvas.width = videoElem.videoWidth;
                            context.drawImage(videoElem, 0, 0, canvas.width, canvas.height);
                            
                            // Aquí se procesaría la imagen para detectar códigos QR
                            // Como es una simulación, simplemente mostramos un mensaje
                            // En una implementación real, se usaría una biblioteca como jsQR
                        }
                    }
                    
                    // Iniciar escaneo
                    scanner = setInterval(scanFrame, scanInterval);
                    
                    startScanBtn.classList.add('d-none');
                    stopScanBtn.classList.remove('d-none');
                })
                .catch(function(err) {
                    scanResult.innerHTML = '<div class="alert alert-danger">Error al acceder a la cámara: ' + err.message + '</div>';
                });
        });
        
        // Detener escaneo
        stopScanBtn.addEventListener('click', function() {
            if (scanner) {
                clearInterval(scanner);
                scanner = null;
                
                const videoElem = document.getElementById('qr-video');
                if (videoElem && videoElem.srcObject) {
                    videoElem.srcObject.getTracks().forEach(track => track.stop());
                }
                
                scannerContainer.innerHTML = '';
                startScanBtn.classList.remove('d-none');
                stopScanBtn.classList.add('d-none');
            }
        });
    }
    
    // Verificación manual de ticket
    const verifyForm = document.getElementById('verify-form');
    if (verifyForm) {
        verifyForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const ticketCode = document.getElementById('ticket-code').value;
            if (!ticketCode) {
                scanResult.innerHTML = '<div class="alert alert-warning">Por favor, ingresa un código de entrada.</div>';
                return;
            }
            
            // Enviar solicitud AJAX para verificar el ticket
            const formData = new FormData(verifyForm);
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            
            fetch(verifyForm.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.valid) {
                    scanResult.innerHTML = '<div class="alert alert-success">' + data.message + '</div>';
                    
                    // Mostrar detalles del ticket
                    ticketDetailsContainer.innerHTML = `
                        <div class="card border-success mb-4">
                            <div class="card-header bg-success text-white">
                                <h5 class="m-0">Detalles de la Entrada</h5>
                            </div>
                            <div class="card-body">
                                <p><strong>Evento:</strong> ${data.ticket.event}</p>
                                <p><strong>Tipo de Entrada:</strong> ${data.ticket.ticket_type}</p>
                                <p><strong>Usuario:</strong> ${data.ticket.user}</p>
                                <p><strong>Fecha de Compra:</strong> ${data.ticket.purchase_date}</p>
                                <p class="mb-0"><strong>Estado:</strong> <span class="badge bg-success">Verificado</span></p>
                            </div>
                        </div>
                    `;
                } else {
                    scanResult.innerHTML = '<div class="alert alert-danger">' + data.message + '</div>';
                    ticketDetailsContainer.innerHTML = '';
                }
            })
            .catch(error => {
                scanResult.innerHTML = '<div class="alert alert-danger">Error al verificar la entrada. Por favor, inténtalo de nuevo.</div>';
                console.error('Error:', error);
            });
        });
    }
});

// Charts for Dashboard (simplified version)
document.addEventListener('DOMContentLoaded', function() {
    const eventSalesChart = document.getElementById('event-sales-chart');
    const ticketTypesChart = document.getElementById('ticket-types-chart');
    
    if (eventSalesChart && typeof Chart !== 'undefined') {
        // Esta es una implementación simplificada. En una aplicación real, 
        // estos datos vendrían del backend con AJAX.
        
        // Gráfico de ventas por evento
        new Chart(eventSalesChart, {
            type: 'bar',
            data: {
                labels: ['Evento 1', 'Evento 2', 'Evento 3', 'Evento 4', 'Evento 5'],
                datasets: [{
                    label: 'Ventas',
                    data: [12, 19, 3, 5, 2],
                    backgroundColor: 'rgba(67, 97, 238, 0.6)',
                    borderColor: 'rgba(67, 97, 238, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    if (ticketTypesChart && typeof Chart !== 'undefined') {
        // Gráfico de tipos de entradas
        new Chart(ticketTypesChart, {
            type: 'pie',
            data: {
                labels: ['VIP', 'General', 'Estudiante'],
                datasets: [{
                    label: 'Entradas Vendidas',
                    data: [30, 50, 20],
                    backgroundColor: [
                        'rgba(67, 97, 238, 0.6)',
                        'rgba(46, 196, 182, 0.6)',
                        'rgba(255, 159, 28, 0.6)'
                    ],
                    borderColor: [
                        'rgba(67, 97, 238, 1)',
                        'rgba(46, 196, 182, 1)',
                        'rgba(255, 159, 28, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true
            }
        });
    }
});

// Animaciones al hacer scroll
document.addEventListener('DOMContentLoaded', function() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    if (animatedElements.length > 0) {
        function checkScroll() {
            animatedElements.forEach(element => {
                const elementTop = element.getBoundingClientRect().top;
                const windowHeight = window.innerHeight;
                
                if (elementTop < windowHeight * 0.8) {
                    element.classList.add('animated');
                }
            });
        }
        
        // Comprobar inicialmente
        checkScroll();
        
        // Comprobar al hacer scroll
        window.addEventListener('scroll', checkScroll);
    }
});