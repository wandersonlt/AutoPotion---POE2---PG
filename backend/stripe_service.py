import stripe
import os
from sqlalchemy.orm import Session
from datetime import datetime
from models import Plan, User, License
from license_service import LicenseService

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

class StripeService:
    
    @staticmethod
    async def create_checkout_session(price_id: str, user_email: str, success_url: str, cancel_url: str):
        """Create a Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription' if 'subscription' in price_id else 'payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=user_email,
                metadata={
                    'user_email': user_email,
                    'price_id': price_id
                }
            )
            return {"session_id": session.id, "url": session.url}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    async def handle_webhook(payload, sig_header, db: Session):
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError:
            return {"error": "Invalid payload"}
        except stripe.error.SignatureVerificationError:
            return {"error": "Invalid signature"}
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await StripeService.handle_successful_payment(session, db)
        
        elif event['type'] == 'invoice.paid':
            invoice = event['data']['object']
            await StripeService.handle_invoice_paid(invoice, db)
        
        return {"status": "success"}
    
    @staticmethod
    async def handle_successful_payment(session, db: Session):
        """Handle successful payment"""
        user_email = session.get('customer_email')
        metadata = session.get('metadata', {})
        
        # Find or create user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            # Create user with temporary username
            username = user_email.split('@')[0]
            base_username = username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            from auth import AuthHandler
            auth = AuthHandler()
            user = User(
                username=username,
                email=user_email,
                password_hash=auth.get_password_hash(os.urandom(24).hex()),
                role="USER"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Determine plan from price
        line_items = stripe.checkout.Session.list_line_items(session['id'])
        if line_items.data:
            price_id = line_items.data[0].price.id
            plan = db.query(Plan).filter(Plan.stripe_price_id == price_id).first()
            
            if plan:
                # Create license
                license = await LicenseService.create_license(user.id, plan.type, db)
                
                # Send email with license (implement email service)
                # await EmailService.send_license_email(user.email, license.key, plan.name)
        
        return True
    
    @staticmethod
    async def handle_invoice_paid(invoice, db: Session):
        """Handle paid invoice for subscriptions"""
        # Extend license validity for subscription renewals
        customer_email = invoice.get('customer_email')
        if customer_email:
            user = db.query(User).filter(User.email == customer_email).first()
            if user:
                license = db.query(License).filter(License.user_id == user.id).first()
                if license:
                    await LicenseService.renew_license(license.id, db)
        
        return True