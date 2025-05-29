// Payment.js - Voor payment.html
document.addEventListener('DOMContentLoaded', function() {
    const checkoutButton = document.getElementById('checkoutButton');
    
    if (checkoutButton) {
        checkoutButton.addEventListener('click', function() {
            // API call naar backend om checkout sessie te maken
            fetch('/payment/create-checkout-session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else if (data.checkout_url) {
                    // Redirect naar Stripe checkout
                    window.location.href = data.checkout_url;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Er is een fout opgetreden bij het starten van de betaling.');
            });
        });
    }
});
