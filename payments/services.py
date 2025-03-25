import requests
import os
import json
import uuid
from django.conf import settings
import logging
import threading
import time
from payments.models import Payment

logger = logging.getLogger(__name__)

class PayPalService:
    """PayPal payment gateway service using Sandbox"""
    
    def __init__(self):
        # PayPal Sandbox API URLs
        self.base_url = os.environ.get('PAYPAL_API_URL', 'https://api-m.sandbox.paypal.com')
        self.client_id = os.environ.get('PAYPAL_CLIENT_ID', '')
        self.client_secret = os.environ.get('PAYPAL_CLIENT_SECRET', '')
    
    def get_access_token(self):
        """Get PayPal OAuth access token for API calls"""
        url = f"{self.base_url}/v1/oauth2/token"
        
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = requests.post(
                url, 
                auth=(self.client_id, self.client_secret),
                data=data,
                headers=headers
            )
            
            response_data = response.json()
            
            if response.status_code != 200:
                logger.error(f"PayPal token error: {response_data}")
                raise Exception("Failed to get PayPal access token")
            
            return response_data["access_token"]
            
        except Exception as e:
            logger.error(f"PayPal token exception: {str(e)}")
            raise Exception(f"PayPal authentication failed: {str(e)}")
    
    def create_order(self, payment):
        """Create a PayPal order"""
        url = f"{self.base_url}/v2/checkout/orders"
        
        access_token = self.get_access_token()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": payment.currency,
                        "value": str(payment.amount)
                    },
                    "description": f"Payment for {payment.customer_name}"
                }
            ],
            "application_context": {
                "return_url": f"{settings.BASE_URL}/api/v1/payments/paypal/success",
                "cancel_url": f"{settings.BASE_URL}/api/v1/payments/paypal/cancel"
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers
            )
            
            response_data = response.json()
            
            if response.status_code not in [200, 201]:
                logger.error(f"PayPal order error: {response_data}")
                raise Exception("Failed to create PayPal order")
            
            # Find the approve link for redirect
            approval_url = next(
                link["href"] for link in response_data["links"] 
                if link["rel"] == "approve"
            )
            
            payment.gateway_response = response_data
            payment.status = "processing"
            payment.save()

            # Start a background thread to verify the payment after 2 seconds
            threading.Thread(target=self._auto_verify_payment, args=(payment.id,), daemon=True).start()
            
            return payment, approval_url
            
        except Exception as e:
            logger.error(f"PayPal order exception: {str(e)}")
            payment.status = "failed"
            payment.save()
            raise Exception(f"PayPal order creation failed: {str(e)}")

    def _auto_verify_payment(self, payment_id):
        """Automatically verify the payment after 2 seconds"""
        time.sleep(2)  # Wait for 2 seconds
        try:
            payment = Payment.objects.get(id=payment_id)
            self.verify_payment(payment)
            logger.info(f"Auto-verified payment {payment.id} with status {payment.status}")
        except Payment.DoesNotExist:
            logger.error(f"Payment {payment_id} does not exist for auto-verification")
        except Exception as e:
            logger.error(f"Error during auto-verification of payment {payment_id}: {str(e)}")
    
    def capture_payment(self, payment):
        """Capture an approved PayPal payment"""
        order_id = payment.gateway_response["id"]
        url = f"{self.base_url}/v2/checkout/orders/{order_id}/capture"
        
        access_token = self.get_access_token()
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        
        try:
            response = requests.post(url, headers=headers)
            response_data = response.json()
            
            if response.status_code not in [200, 201]:
                logger.error(f"PayPal capture error: {response_data}")
                raise Exception("Failed to capture PayPal payment")
            
            # Update payment status to "completed"
            payment.status = "completed"
            payment.gateway_response = response_data
            payment.save()
            
            return response_data
            
        except Exception as e:
            logger.error(f"PayPal capture exception: {str(e)}")
            raise Exception(f"PayPal payment capture failed: {str(e)}")
    
    def verify_payment(self, payment):
        """Verify the status of a PayPal payment"""
        if not payment.gateway_response or "id" not in payment.gateway_response:
            return payment  # Skip verification if no gateway response is available

        order_id = payment.gateway_response["id"]
        url = f"{self.base_url}/v2/checkout/orders/{order_id}"

        access_token = self.get_access_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }

        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()

            if response.status_code != 200:
                logger.error(f"PayPal verification error: {response_data}")
                return payment

            # Update payment status based on PayPal status
            paypal_status = response_data.get("status", "")

            if paypal_status == "COMPLETED":
                payment.status = "completed"
            elif paypal_status == "APPROVED":
                payment.status = "processing"
            elif paypal_status in ["VOIDED", "DECLINED"]:
                payment.status = "failed"

            payment.gateway_response = response_data
            payment.save()

            return payment

        except Exception as e:
            logger.error(f"PayPal verification exception: {str(e)}")
            return payment
