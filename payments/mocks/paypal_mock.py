# def get_paypal_access_token():
#     return {
#         'access_token': 'mock_access_token',
#         'expires_in': 3600
#     }

# def create_payment_mock():
#     return {
#         'id': 'mock_payment_id',
#         'state': 'approved'
#     }

# def mock_paypal_error():
#     return {
#         'error': 'invalid_client',
#         'error_description': 'Client Authentication failed'
#     }

import responses
import json

def mock_paypal_api():
    """Mock PayPal API endpoints."""
    # Mock the token endpoint
    responses.add(
        responses.POST,
        "https://api-m.sandbox.paypal.com/v1/oauth2/token",
        json={"access_token": "mock_access_token", "token_type": "Bearer"},
        status=200
    )

    # Mock the create order endpoint
    responses.add(
        responses.POST,
        "https://api-m.sandbox.paypal.com/v2/checkout/orders",
        json={
            "id": "mock_order_id",
            "status": "CREATED",
            "links": [
                {"href": "https://mock-approval-url.com", "rel": "approve"}
            ]
        },
        status=201
    )

    # Mock the capture payment endpoint
    responses.add(
        responses.POST,
        "https://api-m.sandbox.paypal.com/v2/checkout/orders/mock_order_id/capture",
        json={"status": "COMPLETED"},
        status=201
    )