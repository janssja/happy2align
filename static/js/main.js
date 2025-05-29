// Main.js - Voor algemene functionaliteit
document.addEventListener('DOMContentLoaded', function() {
    // Algemene functionaliteit voor alle pagina's
    console.log('Happy 2 Align applicatie geladen');
    
    // Voeg animaties toe aan alerts
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
});
