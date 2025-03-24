
# Create your tests here.
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
import uuid
import responses
from .mocks.paypal_mock import mock_paypal_api
from .models import Payment



class PaymentAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create a test payment
        self.test_payment = Payment.objects.create(
            customer_name="Test User",
            customer_email="test@example.com",
            amount=100.00,
            currency="USD",
            status="completed",
            reference_id="test-reference"
        )
    
    @responses.activate
    def test_create_payment(self):
        """Test creating a new payment"""
        mock_paypal_api()

        url = reverse('initiate-payment')
        data = {
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "amount": 50.00,
            "currency": "USD",
            "gateway": "paypal"
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['payment']['customer_name'], 'John Doe')
        self.assertEqual(float(response.data['payment']['amount']), 50.00)
    
    def test_get_payment(self):
        """Test retrieving an existing payment"""
        url = reverse('payment-detail', args=[self.test_payment.id])
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertEqual(response.data['payment']['customer_name'], 'Test User')
        self.assertEqual(response.data['payment']['status'], 'completed')
    
    def test_get_nonexistent_payment(self):
        """Test retrieving a non-existent payment"""
        # Generate a random UUID that doesn't exist
        random_id = uuid.uuid4()
        url = reverse('payment-detail', args=[random_id])
        
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_payment_data(self):
        """Test creating a payment with invalid data"""
        url = reverse('initiate-payment')
        data = {
            "customer_name": "John Doe",
            # Missing email
            "amount": -50.00,  # Invalid amount
            "gateway": "invalid_gateway"  # Invalid gateway
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['status'], 'error')