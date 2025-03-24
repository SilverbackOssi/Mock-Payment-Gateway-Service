import requests
import os
import json
import uuid
from django.conf import settings
import logging

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
            
            payment.reference_id = response_data["id"]
            payment.status = "processing"
            payment.gateway_response = response_data
            payment.save()
            
            return payment, approval_url
            
        except Exception as e:
            logger.error(f"PayPal order exception: {str(e)}")
            payment.status = "failed"
            payment.save()
            raise Exception(f"PayPal order creation failed: {str(e)}")
    
    def capture_payment(self, order_id):
        """Capture an approved PayPal payment"""
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
            
            return response_data
            
        except Exception as e:
            logger.error(f"PayPal capture exception: {str(e)}")
            raise Exception(f"PayPal payment capture failed: {str(e)}")
    
    def verify_payment(self, payment):
        """Verify the status of a PayPal payment"""
        if not payment.reference_id:
            return payment
            
        url = f"{self.base_url}/v2/checkout/orders/{payment.reference_id}"
        
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