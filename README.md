# Payment Gateway API with PayPal

A RESTful API for small businesses to accept payments from customers using PayPal Sandbox.

## Features

- Process payments with minimal customer information (name, email, amount)
- Integration with PayPal Sandbox for testing
- RESTful API with versioning
- Automated testing and deployment through CI/CD

## API Endpoints

### Initiate a Payment

```
POST /api/v1/payments
```

**Request Body:**

```json
{
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "amount": 50.00,
  "currency": "USD"
}
```

**Response:**

```json
{
  "payment": {
    "id": "PAY-12345678",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "amount": 50.00,
    "currency": "USD",
    "status": "processing"
  },
  "redirect_url": "https://www.sandbox.paypal.com/checkoutnow?token=ABC123XYZ",
  "status": "success",
  "message": "Payment initiated successfully. Redirect the customer to complete payment."
}
```

### Get Payment Status

```
GET /api/v1/payments/{id}
```

**Response:**

```json
{
  "payment": {
    "id": "PAY-12345678",
    "customer_name": "John Doe",
    "customer_email": "john@example.com",
    "amount": 50.00,
    "currency": "USD",
    "status": "completed"
  },
  "status": "success",
  "message": "Payment details retrieved successfully."
}
```

## PayPal Integration Flow

1. Customer submits payment information
2. Your server initiates a PayPal payment and receives a redirect URL
3. Redirect the customer to the PayPal page to complete payment
4. PayPal redirects back to your success/cancel endpoints
5. Your server captures the payment and updates the status

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- PayPal Developer Account with Sandbox credentials

### PayPal Sandbox Setup

1. Create a PayPal Developer account at [developer.paypal.com](https://developer.paypal.com)
2. Create a Sandbox app to get your CLIENT_ID and CLIENT_SECRET
3. Set up a Sandbox account for testing

### Local Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/payment-gateway-api.git
   cd payment-gateway-api
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the project root with the following variables:
   ```
   DEBUG=True
   SECRET_KEY=your_secret_key
   DATABASE_URL=postgres://user:password@localhost:5432/payment_gateway_db
   BASE_URL=http://localhost:8000
   
   # PayPal Sandbox API Credentials
   PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
   PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
   PAYPAL_API_URL=https://api-m.sandbox.paypal.com
   ```

5. Apply migrations:
   ```
   python manage.py migrate
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

## Testing

### Manual Testing with PayPal Sandbox

1. Use the `/api/v1/payments` endpoint to create a payment
2. Use the returned `redirect_url` to simulate a customer payment
3. Log in with your PayPal Sandbox buyer account
4. Complete the payment
5. PayPal will redirect to your success URL
6. Check the payment status using the payment ID

### Automated Testing

Run the tests with:

```
python manage.py test
```

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

1. **Test**: Runs the Django test suite on each push and pull request
2. **Deploy**: Automatically deploys to Render when changes are pushed to the main branch

## Going to Production

When ready to move to production:

1. Create a PayPal live account and obtain production credentials
2. Update your environment variables with the production credentials
3. Change the PayPal API URL to the production endpoint
4. Ensure your server has HTTPS enabled for secure payments
5. Thoroughly test the payment flow before going live

## License

This project is licensed under the MIT License - see the LICENSE file for details.