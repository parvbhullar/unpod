import decimal
from rest_framework import serializers
from unpod.common.constants import DATETIME_FORMAT
from unpod.core_components.utils import get_user_data
from unpod.wallet.models import (
    BitConvertorModel,
    BitsTransaction,
    Order,
    PaymentGatewayTransactions,
)
from unpod.subscription.models import ActiveSubscription
from unpod.common.datetime import get_datetime_now
from unpod.wallet.services import (
    getWallet,
    increment_order_number,
)
from unpod.wallet.enum import (
    BitsTransactionType,
    BitsTransactionVia,
    PaymentMethodEnum,
    TransactionEnum,
)


class OrderModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"

    def create(self, validated_data):
        app_user = self.context["request"].user
        validated_data["updated_by"] = app_user.id
        validated_data["created_by"] = app_user.id

        order_data = {
            **validated_data,
            "user_id": app_user.id,
            "organization_id": app_user.organization.id,
            "order_number": increment_order_number(Order),
            "receipt_number": None,
            "payment_mode": PaymentMethodEnum.razorpay.name,
            "order_date": get_datetime_now(),
        }

        instance = self.Meta.model.objects.create(**order_data)
        return instance


class BitsTransactionRechargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BitsTransaction
        fields = (
            "id",
            "parent",
            "user",
            "referral_user",
            "object_type",
            "object_id",
            "transaction_type",
            "transaction_via",
            "bits",
            "order",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "record_status",
        )

    def calculateBit(self, amount, currency):
        unit_value = 1
        obj = BitConvertorModel.objects.filter(currency=currency).first()
        if obj:
            unit_value = obj.unit_value
        bit_amount = round((decimal.Decimal(amount) / unit_value), 6)
        return bit_amount, unit_value

    def onCompleteRecharge(self, validated_data):
        app_user = self.context["request"].user
        if app_user:
            validated_data["updated_by"] = app_user.id
            validated_data["created_by"] = app_user.id
        else:
            validated_data["updated_by"] = None
            validated_data["created_by"] = None
        user_wallet = getWallet(app_user)
        # print(validated_data, 'validated_data')

        if validated_data is not None:
            bits, unit_value = self.calculateBit(
                validated_data.get("amount"), validated_data.get("currency")
            )
            transaction_data = {
                "parent": None,
                "user_id": app_user.id,
                "organization_id": app_user.organization.id,
                "transaction_type": BitsTransactionType.added.name,
                "transaction_via": BitsTransactionVia.recharge.name,
                "updated_by": app_user.id,
                "created_by": app_user.id,
                "transaction_date": get_datetime_now(),
                "bits": bits,
                "currency_value": unit_value,
                "currency": validated_data.get("currency"),
            }
            order = Order.objects.filter(
                online_order_id=validated_data.get("online_order_id")
            ).first()
            if order:
                order.updated_by = app_user.id
                order.order_status = TransactionEnum.success.name
                order.save()
            transaction = BitsTransaction.objects.create(**transaction_data)
            user_wallet.bits += transaction.bits
            user_wallet.last_tranaction = transaction
            user_wallet.save()
        return transaction


class BitsTransactionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = BitsTransaction
        fields = (
            "id",
            "parent",
            "user",
            "referral_user",
            "object_type",
            "object_id",
            "transaction_type",
            "transaction_via",
            "bits",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )

    def get_referral_user(self, obj):
        return None


class VerifyPaymentSerializer(serializers.Serializer):
    payment_response = serializers.JSONField()
    order_id = serializers.CharField(max_length=100)
    currency = serializers.CharField(max_length=100)
    amount = serializers.FloatField()


class VerifySubscriptionSerializer(serializers.Serializer):
    payment_response = serializers.JSONField()
    subscription_id = serializers.CharField(max_length=100)


class RecordPaymentSerializer(serializers.Serializer):
    pay_response = serializers.JSONField()
    pay_type = serializers.CharField(max_length=10)


class PaymentTransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentGatewayTransactions
        fields = "__all__"


class BitsTransactionSerializer(serializers.ModelSerializer):
    transaction_type = serializers.SerializerMethodField()
    transaction_via = serializers.SerializerMethodField()
    transaction_date = serializers.DateTimeField(format=DATETIME_FORMAT)
    desc = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = BitsTransaction
        fields = (
            "transaction_type",
            "transaction_via",
            "bits",
            "transaction_date",
            "currency",
            "currency_value",
            "desc",
            "user",
        )

    def get_transaction_type(self, obj):
        return BitsTransactionType[obj.transaction_type].value

    def get_transaction_via(self, obj):
        return BitsTransactionVia[obj.transaction_via].value

    def get_desc(self, obj):
        if obj.transaction_via == BitsTransactionVia.joining_bonus.name:
            return "Sign Up Bonus"
        if obj.transaction_via == BitsTransactionVia.referral_bonus.name:
            message = f"Referral Bonus"
            return message
        return ""

    def get_user(self, instance):
        return get_user_data(
            instance.user,
            fields=[
                "email",
                "full_name",
                "user_token",
                "profile_color",
                "profile_picture",
            ],
        )


class ActiveSubscriptionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActiveSubscription
        fields = [
            "organization",
            "is_active",
            "valid_from",
            "valid_to",
            "subscription_metadata",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        subscription_metadata = representation.get("subscription_metadata", {})
        representation["subscription_details"] = subscription_metadata.pop(
            "subscription_details", {}
        )
        representation["subscription_id"] = subscription_metadata.pop(
            "subscription_id", None
        )
        representation["subscription_name"] = subscription_metadata.pop(
            "subscription_name", None
        )
        return representation


class AddOnSubscribeItemSerializer(serializers.Serializer):
    codename = serializers.CharField(required=True, max_length=100)
    quantity = serializers.IntegerField(required=True, min_value=0)
