// QR Scanner implementation
document.addEventListener('DOMContentLoaded', function() {
    const scannerContainer = document.getElementById('qr-scanner');
    const startScanBtn = document.getElementById('start-scan');
    const stopScanBtn = document.getElementById('stop-scan');
    const scanResult = document.getElementById('scan-result');
    const ticketDetailsContainer = document.getElementById('ticket-details');
    const ticketCodeInput = document.getElementById('ticket-code');
    
    // Verificar si los elementos existen
    if (!(scannerContainer && startScanBtn && stopScanBtn)) {
        return;
    }
    
    let scanner = null;
    let videoStream = null;
    
    // Función para procesar el código QR encontrado
    function processQRCode(code) {
        if (ticketCodeInput) {
            ticketCodeInput.value = code;
            // Disparar evento de envío del formulario
            document.getElementById('verify-form').dispatchEvent(new Event('submit'));
        }
    }
    
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
        
        // Importar dinámicamente la biblioteca jsQR
        scannerContainer.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Cargando...</span></div><p>Inicializando cámara...</p></div>';
        
        // Cargar la biblioteca jsQR
        const jsQRScript = document.createElement('script');
        jsQRScript.src = 'https://cdn.jsdelivr.net/npm/jsqr@1.4.0/dist/jsQR.min.js';
        document.head.appendChild(jsQRScript);
        
        jsQRScript.onload = function() {
            // Mostrar elemento de video
            scannerContainer.innerHTML = '<video id="qr-video" class="w-100" style="max-height: 300px;"></video>';
            const videoElem = document.getElementById('qr-video');
            
            // Solicitar acceso a la cámara
            navigator.mediaDevices.getUserMedia({ 
                video: { 
                    facingMode: "environment",
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                }
            })
            .then(function(stream) {
                videoStream = stream;
                videoElem.srcObject = stream;
                videoElem.setAttribute("playsinline", true);
                videoElem.play();
                
                // Crear un canvas para capturar frames
                const canvas = document.createElement('canvas');
                const context = canvas.getContext('2d');
                const scanInterval = 200; // Escanear cada 200ms
                
                // Función para escanear un frame
                function scanFrame() {
                    if (videoElem.readyState === videoElem.HAVE_ENOUGH_DATA) {
                        canvas.height = videoElem.videoHeight;
                        canvas.width = videoElem.videoWidth;
                        context.drawImage(videoElem, 0, 0, canvas.width, canvas.height);
                        
                        const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
                        const code = jsQR(imageData.data, imageData.width, imageData.height, {
                            inversionAttempts: "dontInvert",
                        });
                        
                        if (code) {
                            // QR encontrado, procesar
                            processQRCode(code.data);
                            
                            // Opcionalmente, detener el escáner después de encontrar un código
                            // stopScanner();
                        }
                    }
                }
                
                // Iniciar escaneo
                scanner = setInterval(scanFrame, scanInterval);
                
                startScanBtn.classList.add('d-none');
                stopScanBtn.classList.remove('d-none');
            })
            .catch(function(err) {
                scanResult.innerHTML = '<div class="alert alert-danger">Error al acceder a la cámara: ' + err.message + '</div>';
                console.error('Error de cámara:', err);
            });
        };
    });
    
    // Función para detener el escáner
    function stopScanner() {
        if (scanner) {
            clearInterval(scanner);
            scanner = null;
            
            if (videoStream) {
                videoStream.getTracks().forEach(track => track.stop());
                videoStream = null;
            }
            
            scannerContainer.innerHTML = '<div class="text-center p-4 bg-light"><i class="fas fa-camera fa-3x mb-3 text-muted"></i><p>Haz clic en "Iniciar Escáner" para escanear un código QR</p></div>';
            startScanBtn.classList.remove('d-none');
            stopScanBtn.classList.add('d-none');
        }
    }
    
    // Detener escaneo
    stopScanBtn.addEventListener('click', stopScanner);
});