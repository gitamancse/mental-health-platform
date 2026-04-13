import logging
import uuid

logger = logging.getLogger(__name__)

class PaymentGatewayService:
    """
    Generic Payment Gateway Adapter.
    This will be updated with the specific logic for whichever 
    provider the client chooses (Stripe, PayPal, Braintree, etc.)
    """
    @staticmethod
    async def initialize_subscription(email: str, full_name: str, token: str):
        """
        Placeholder for initializing a subscription/trial.
        """
        logger.info(f"[PAYMENT GATEWAY] Initializing billing for {email}")
        
        # Generate generic placeholder IDs
        external_customer_id = f"cust_{uuid.uuid4().hex[:12]}"
        external_subscription_id = f"sub_{uuid.uuid4().hex[:12]}"
        
        return external_customer_id, external_subscription_id