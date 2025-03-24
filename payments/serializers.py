from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'customer_name', 'customer_email', 'amount', 'currency', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['customer_name', 'customer_email', 'amount', 'currency']
        
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
        
    def validate_currency(self, value):
        allowed_currencies = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
        if value not in allowed_currencies:
            raise serializers.ValidationError(f"Currency must be one of {', '.join(allowed_currencies)}")
        return value

class PaymentResponseSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    
    class Meta:
        model = Payment
        fields = ['id', 'customer_name', 'customer_email', 'amount', 'currency', 'status']
        
    def get_id(self, obj):
        return f"PAY-{str(obj.id)[:8]}"