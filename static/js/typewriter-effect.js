// Archivo: static/js/typewriter-effect.js

/**
 * Script para el efecto de máquina de escribir (Typewriter)
 * con cambio automático de frases
 */
document.addEventListener('DOMContentLoaded', function() {
    // Frases para cada tipo de usuario
    const phrases = {
        'guest-description': [
            'Encuentra los mejores eventos en un solo lugar',
            'Vive experiencias únicas e inolvidables',
            'Compra entradas de forma segura y rápida',
            'Descubre eventos exclusivos cerca de ti'
        ],
        'user-description': [
            'Tus experiencias te esperan, descubre eventos únicos',
            'Explora, reserva y asiste a los mejores eventos',
            'Entradas digitales en un solo lugar',
            'Tu agenda de eventos personalizada'
        ],
        'admin-description': [
            'Gestiona eventos, tickets y usuarios con herramientas avanzadas',
            'Monitorea las ventas y estadísticas en tiempo real',
            'Controla accesos y verifica entradas fácilmente',
            'Administra la plataforma de eventos completa'
        ]
    };
    
    // Para cada elemento con efecto typewriter
    Object.keys(phrases).forEach(elementId => {
        const element = document.getElementById(elementId);
        
        if (element) {
            const currentPhrases = phrases[elementId];
            let phraseIndex = 0;
            
            // Función para cambiar el texto con efecto typewriter
            function typeWriter() {
                const currentPhrase = currentPhrases[phraseIndex];
                let charIndex = 0;
                
                // Limpiar el elemento
                element.textContent = '';
                element.classList.remove('typewriter');
                void element.offsetWidth; // Trigger reflow (reiniciar animación)
                element.classList.add('typewriter');
                
                // Función para escribir el texto letra por letra
                function type() {
                    if (charIndex < currentPhrase.length) {
                        element.textContent += currentPhrase.charAt(charIndex);
                        charIndex++;
                        setTimeout(type, 70); // Velocidad de escritura
                    } else {
                        // Esperar antes de borrar y escribir la siguiente frase
                        setTimeout(() => {
                            phraseIndex = (phraseIndex + 1) % currentPhrases.length;
                            setTimeout(typeWriter, 500); // Tiempo entre frases
                        }, 3000); // Tiempo que se muestra la frase completa
                    }
                }
                
                type(); // Iniciar la escritura
            }
            
            // Iniciar el efecto
            typeWriter();
        }
    });
    
    // Animaciones al hacer scroll
    const animatedElements = document.querySelectorAll('.fade-in, .bounce, .card-hover');
    
    function checkScroll() {
        animatedElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementTop < windowHeight * 0.9) {
                element.style.opacity = "1";
                element.classList.add('animated');
            }
        });
    }
    
    // Comprobar inicialmente y al hacer scroll
    checkScroll();
    window.addEventListener('scroll', checkScroll);
});