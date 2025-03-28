from django.urls import path
from .views import InitiatePaymentView, PaymentDetailView, PayPalSuccessView, PayPalCancelView, PaymentListView, DocumentationView

urlpatterns = [
    path('', DocumentationView.as_view(), name='default-page'),
    path('v1/payments/', InitiatePaymentView.as_view(), name='initiate-payment'),
    path('v1/payments/all/', PaymentListView.as_view(), name='payment-list'),  
    path('v1/payments/<uuid:id>/', PaymentDetailView.as_view(), name='payment-detail'),
    path('v1/payments/paypal/success/', PayPalSuccessView.as_view(), name='paypal-success'),
    path('v1/payments/paypal/cancel/', PayPalCancelView.as_view(), name='paypal-cancel'),
]

'''

urlpatterns = [
    path('initiate-payment/', views.InitiatePaymentView.as_view(), name='initiate-payment'),
    path('payments/<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
]
'''
