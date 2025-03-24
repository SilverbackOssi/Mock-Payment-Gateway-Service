from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, redirect
from django.http import Http404
from .models import Payment
from .serializers import PaymentSerializer, PaymentCreateSerializer, PaymentResponseSerializer
from .services import PayPalService
import logging

from django.conf import settings
from payments.mocks.paypal_mock import mock_paypal_api

if settings.DEBUG:
    import responses
    responses.start()
    mock_paypal_api()

logger = logging.getLogger(__name__)

class InitiatePaymentView(APIView):
    """
    API endpoint for initiating a PayPal payment
    """
    def post(self, request, format=None):
        serializer = PaymentCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            # Save the payment with initial pending status
            payment = serializer.save(status='pending')
            
            try:
                # Process the payment with PayPal
                paypal_service = PayPalService()
                processed_payment, approval_url = paypal_service.create_order(payment)
                
                # Prepare the response
                response_serializer = PaymentResponseSerializer(processed_payment)
                
                return Response({
                    "payment": response_serializer.data,
                    "redirect_url": approval_url,
                    "status": "success",
                    "message": "Payment initiated successfully. Redirect the customer to complete payment."
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                # If there's an error, update the payment status and return an error
                payment.status = 'failed'
                payment.save()
                
                logger.error(f"Payment initiation error: {str(e)}")
                
                return Response({
                    "status": "error",
                    "message": f"Payment processing failed: {str(e)}"
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "status": "error",
            "message": "Invalid payment data",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class PaymentDetailView(APIView):
    """
    API endpoint for retrieving payment details
    """
    def get(self, request, id, format=None):
        try:
            # Find the payment by ID
            payment = get_object_or_404(Payment, id=id)
            
            # If the payment is still processing, check its status
            if payment.status in ['pending', 'processing']:
                try:
                    # Verify the payment status with PayPal
                    paypal_service = PayPalService()
                    payment = paypal_service.verify_payment(payment)
                except Exception as e:
                    logger.error(f"Payment verification error: {str(e)}")
                    # If verification fails, just continue with the current payment status
                    pass
            
            # Prepare the response
            response_serializer = PaymentResponseSerializer(payment)
            
            return Response({
                "payment": response_serializer.data,
                "status": "success",
                "message": "Payment details retrieved successfully."
            }, status=status.HTTP_200_OK)
            
        except Http404:
            return Response({
                "status": "error",
                "message": "Payment not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Payment detail error: {str(e)}")
            return Response({
                "status": "error",
                "message": f"Error retrieving payment details: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentListView(APIView):
    """
    API endpoint for retrieving all payments
    """
    def get(self, request, format=None):
        try:
            # Retrieve all payments
            payments = Payment.objects.all()
            
            # Serialize the payments
            serializer = PaymentSerializer(payments, many=True)
            
            return Response({
                "payments": serializer.data,
                "status": "success",
                "message": "All payments retrieved successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving all payments: {str(e)}")
            return Response({
                "status": "error",
                "message": f"Error retrieving payments: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PayPalSuccessView(APIView):
    """
    Webhook endpoint for successful PayPal payments
    """
    def get(self, request, format=None):
        order_id = request.query_params.get('token')
        
        if not order_id:
            return Response({
                "status": "error",
                "message": "No order ID provided."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find the payment by PayPal order ID
            payment = get_object_or_404(Payment, reference_id=order_id)
            
            # Capture the payment
            paypal_service = PayPalService()
            capture_result = paypal_service.capture_payment(order_id)
            
            # Update payment status
            payment.status = "completed"
            payment.gateway_response = capture_result
            payment.save()
            
            # Return success page or redirect to frontend
            return Response({
                "status": "success",
                "message": "Payment completed successfully.",
                "payment_id": str(payment.id)
            }, status=status.HTTP_200_OK)
            
        except Http404:
            return Response({
                "status": "error",
                "message": "Payment not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"PayPal success callback error: {str(e)}")
            return Response({
                "status": "error",
                "message": f"Error completing payment: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PayPalCancelView(APIView):
    """
    Webhook endpoint for cancelled PayPal payments
    """
    def get(self, request, format=None):
        order_id = request.query_params.get('token')
        
        if not order_id:
            return Response({
                "status": "error",
                "message": "No order ID provided."
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find the payment by PayPal order ID
            payment = get_object_or_404(Payment, reference_id=order_id)
            
            # Update payment status
            payment.status = "failed"
            payment.save()
            
            # Return cancel page or redirect to frontend
            return Response({
                "status": "cancelled",
                "message": "Payment was cancelled.",
                "payment_id": str(payment.id)
            }, status=status.HTTP_200_OK)
            
        except Http404:
            return Response({
                "status": "error",
                "message": "Payment not found."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"PayPal cancel callback error: {str(e)}")
            return Response({
                "status": "error",
                "message": f"Error processing payment cancellation: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
