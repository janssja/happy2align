from flask import Blueprint, request, jsonify, session
from src.models import db
from src.models.payment import Payment
from src.models.user import User
from functools import wraps
import stripe
import os

payment_bp = Blueprint('payment', __name__)

# Stripe configuratie
stripe.api_key = os.getenv('STRIPE_API_KEY', 'sk_test_example')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Niet ingelogd'}), 401
        return f(*args, **kwargs)
    return decorated_function

@payment_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    try:
        user = User.query.get(session['user_id'])
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {
                            'name': '49 Credits voor Happy 2 Align',
                            'description': 'Toegang tot 49 sessies met Happy 2 Align',
                        },
                        'unit_amount': 4900,  # €49.00
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.host_url + 'payment/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'payment/cancel',
            client_reference_id=str(user.id),
        )
        
        return jsonify({'checkout_url': checkout_session.url})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET', 'whsec_example')
        )
    except ValueError as e:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Verwerk checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session_data = event['data']['object']
        
        # Haal gebruiker op
        user_id = int(session_data['client_reference_id'])
        user = User.query.get(user_id)
        
        if user:
            # Voeg credits toe aan gebruiker
            user.add_credits(49)
            
            # Maak betalingsrecord aan
            payment = Payment(
                user_id=user.id,
                amount=49.00,
                credits=49,
                payment_method='stripe',
                transaction_id=session_data['id']
            )
            
            db.session.add(payment)
            db.session.commit()
    
    return jsonify({'success': True})

@payment_bp.route('/success', methods=['GET'])
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    
    try:
        # Verifieer de sessie
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Controleer of de sessie bij de huidige gebruiker hoort
        if int(checkout_session['client_reference_id']) != session['user_id']:
            return jsonify({'error': 'Ongeautoriseerd'}), 401
        
        return jsonify({
            'message': 'Betaling succesvol',
            'credits_added': 49
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/cancel', methods=['GET'])
@login_required
def payment_cancel():
    return jsonify({'message': 'Betaling geannuleerd'})

@payment_bp.route('/history', methods=['GET'])
@login_required
def payment_history():
    user_id = session['user_id']
    payments = Payment.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'payments': [payment.to_dict() for payment in payments]
    })
