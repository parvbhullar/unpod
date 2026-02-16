import traceback

from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated

from unpod.common.datetime import get_datetime_now
from unpod.common.exception import APIException206
from unpod.common.helpers.calculation_helper import extract_number
from unpod.common.renderers import UnpodJSONRenderer
from unpod.common.serializer import CommonSerializer
from rest_framework.response import Response
from django.utils import timezone
from unpod.common.utils import complete_message
from unpod.space.services import get_organization_by_domain_handle
from unpod.subscription.services import (
    find_by_codename,
    createActiveSubscription,
    expire_active_subscription,
    assign_addons_to_subscription,
    get_subscription_info,
    get_subscription_modules,
    prepare_subscription_metadata,
)
from unpod.wallet.constants import ACTIVE_HIGHER_ERROR
from unpod.wallet.models import (
    BitConvertorModel,
    BitsTransaction,
    Order,
    PaymentGatewayTransactions,
)
from unpod.wallet.enum import (
    TransactionEnum,
    CurrencyEnum,
    BitsTransactionType,
    BitsTransactionVia,
)
from unpod.wallet.serializers import (
    BitsTransactionRechargeSerializer,
    BitsTransactionSerializer,
    OrderModelSerializer,
    PaymentTransactionsSerializer,
    RecordPaymentSerializer,
    VerifyPaymentSerializer,
    ActiveSubscriptionDetailSerializer,
    AddOnSubscribeItemSerializer,
)
from unpod.wallet.razorpay import unpodRazorPay
from unpod.common.validation import Validation
from unpod.wallet.services import (
    calculateBit,
    checkActiveSubscription,
    convertCurrency,
    getWallet,
    getActiveSubscription,
)
from unpod.subscription.models import (
    Subscription,
    SubscriptionInvoice,
    ActiveSubscription,
)
from unpod.wallet.utils import create_payment_order


class UserWalletViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = (UnpodJSONRenderer,)

    def get(self, request):
        obj = getWallet(request.user)
        if obj:
            return Response({"bits": obj.bits}, status=200)
        return Response({"bits": 0}, status=200)


class BitValueViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = (UnpodJSONRenderer,)

    def get(self, request):
        default_data = {"unit_value": 75, "currency": CurrencyEnum.INR.name}
        currency = request.GET.get("currency", "INR")
        obj = (
            BitConvertorModel.objects.filter(currency=currency)
            .values("unit_value", "currency")
            .last()
        )
        if obj:
            return Response(obj, status=200)
        return Response(default_data, status=200)


class BitsTransactionViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = (UnpodJSONRenderer,)

    def get(self, request):
        bitTransaction = (
            BitsTransaction.objects.filter(organization=request.user.organization)
            .select_related("order", "user")
            .order_by("-transaction_date")[:30]
        )
        data = BitsTransactionSerializer(bitTransaction, many=True).data
        return Response(data, status=200)


class RazorPaymentAPI(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = (UnpodJSONRenderer,)

    def createOrder(self, request):
        require_field = ["amount", "currency"]
        validation = Validation(require_field, request.data, {"notes": dict()})
        if not validation.check_required_fields():
            return Response({"error": validation.get_error()}, status=206)
        validation.setData()
        input_data = validation.get_data()
        input_data["order_type"] = "credits"
        ser = OrderModelSerializer(data=input_data, context={"request": request})

        if ser.is_valid(raise_exception=True):
            order_obj = ser.save()

            razorpay_obj = create_payment_order(order_obj)
            order_obj.online_order_id = razorpay_obj["id"]
            order_obj.save()

            return Response(razorpay_obj, status=200)
        return Response(
            {"message": "There is some Validation errors", "errors": ser.errors},
            status=206,
        )

    def calculateBits(self, request):
        amount = request.data.get("amount")
        currency = request.data.get("currency", "INR")
        if amount is None:
            return Response({"errors": "Amount is required."}, status=206)

        bit_value = (
            BitConvertorModel.objects.filter(currency=currency)
            .values("unit_value")
            .last()
        )
        if not bit_value:
            return Response({"errors": "Currency not found."}, status=206)

        unit_value = bit_value["unit_value"]
        calculated_bits = amount / unit_value

        wallet = getWallet(request.user)
        if wallet:
            wallet.bits += calculated_bits
            wallet.save()
            BitsTransaction.objects.create(
                user=request.user,
                amount=amount,
                bits=calculated_bits,
                organization=request.user.organization,
            )
            return Response(
                {
                    "message": "Successfully added bits.",
                    "calculated_bits": calculated_bits,
                },
                status=200,
            )

        return Response({"error": "Wallet not found."}, status=206)

    def completeTransaction(self, data):
        final_data = {**data}
        bitSer = BitsTransactionRechargeSerializer(
            data=final_data, context={"request": self.request}
        )
        try:
            instance = bitSer.onCompleteRecharge(final_data)
        except Exception as e:
            print(str(e))
            traceback.print_exc()
            return Response({"message": str(e)}, status=206)
        return Response({"message": "Payment Completed"}, status=200)

    def transaction(self, request):
        print("\n=== Starting transaction process ===")
        print(f"Request data: {request.data}")

        data = request.data.get("payload", {})
        print(f"Payload data: {data}")

        serializer = VerifyPaymentSerializer(data=data)

        if not serializer.is_valid():
            print(f"Validation errors: {serializer.errors}")
            return Response(
                {
                    "message": "There is some Validation error",
                    "errors": serializer.errors,
                },
                status=206,
            )

        try:
            ser_data = serializer.data
            print(f"Serialized data: {ser_data}")

            # Extract payment details
            payment_response = ser_data.get("payment_response", {})
            order_id = payment_response.get("razorpay_order_id")
            payment_id = payment_response.get("razorpay_payment_id")
            razorpay_signature = payment_response.get("razorpay_signature")
            razorpay_amount = ser_data.get("amount")
            razorpay_currency = ser_data.get("currency")

            print(f"Order ID: {order_id}")
            print(f"Payment ID: {payment_id}")
            print(f"Amount: {razorpay_amount} {razorpay_currency}")

            # Verify the signature
            print("Verifying payment signature...")
            signature = unpodRazorPay.verifySignature(
                payment_id, order_id, razorpay_signature
            )
            print(f"Signature verification: {'Success' if signature else 'Failed'}")

            if not signature:
                return Response({"message": "Invalid payment signature"}, status=206)

            # Fetch payment details from Razorpay
            print(f"Fetching payment details for ID: {payment_id}")
            payment = unpodRazorPay.client.payment.fetch(payment_id)
            print(f"Payment details: {payment}")

            if not payment:
                return Response({"message": "Payment not found"}, status=206)

            payment_status = payment.get("status")
            if payment_status not in ["authorized", "captured"]:
                print(
                    f"Payment status is not 'authorized' or 'captured'. Current status: {payment_status}"
                )
                return Response(
                    {
                        "message": f"Payment not in valid state. Current status: {payment_status}"
                    },
                    status=206,
                )

            # If payment is already captured, skip the capture step
            if payment_status == "captured":
                print("Payment already captured, proceeding with order completion...")
            else:
                # Only attempt to capture if payment is authorized
                print("Attempting to capture payment...")
                res = unpodRazorPay.razorpayCapture(
                    payment_id, razorpay_amount, razorpay_currency
                )
                print(f"Capture response: {res}")

            # Find or create the order record
            try:
                order = Order.objects.get(online_order_id=order_id)
                print(f"Found existing order: {order.id}")
            except Order.DoesNotExist:
                print(f"No order found with ID: {order_id}, creating new order...")

                # Get valid choices for payment_mode and order_status
                from unpod.wallet.models import PaymentMethodEnum, TransactionEnum

                # Use the default razorpay payment method
                # since PaymentMethodEnum only has 'razorpay' as an option
                payment_mode = PaymentMethodEnum.razorpay.name

                # Prepare order data according to the model
                order_data = {
                    "online_order_id": order_id,
                    "amount": float(payment.get("amount", 0))
                    / 100,  # Convert from paise to rupees
                    "currency": payment.get("currency", "INR"),
                    "order_type": "credits",
                    "order_status": TransactionEnum.success.name,  # Use the correct status from your enum
                    "payment_mode": payment_mode,  # Use the predefined payment mode
                    "order_date": timezone.now(),
                    "notes": f"Created from Razorpay payment {payment_id}",
                    "order_metadata": {
                        "payment_id": payment_id,
                        "payment_status": payment.get("status"),
                        "payment_details": payment,
                        "razorpay_order_id": order_id,
                        "razorpay_payment_id": payment_id,
                        "created_from": "payment_completion",
                        "original_payment_method": payment.get(
                            "method", "unknown"
                        ),  # Store original method in metadata
                    },
                }

                # Create the order using the serializer
                try:
                    order_serializer = OrderModelSerializer(
                        data=order_data, context={"request": request}
                    )

                    if order_serializer.is_valid():
                        order = order_serializer.save()
                        print(f"Created new order: {order.id}")
                    else:
                        print(f"Error creating order: {order_serializer.errors}")
                        return Response(
                            {
                                "message": "Error creating order",
                                "errors": order_serializer.errors,
                            },
                            status=400,
                        )

                except Exception as e:
                    print(f"Exception while creating order: {str(e)}")
                    print(traceback.format_exc())
                    return Response(
                        {"message": f"Error creating order: {str(e)}"}, status=400
                    )

            # Convert order to dict for completeTransaction
            complete_data = {
                "id": order.id,
                "online_order_id": order.online_order_id,
                "amount": float(order.amount),
                "currency": order.currency,
                "order_status": order.order_status,  # Changed from status to order_status
                "payment_mode": order.payment_mode,  # Changed from payment_method to payment_mode
                "order_date": order.order_date.isoformat()
                if order.order_date
                else None,
                "user_id": order.user_id,
                "organization_id": order.organization_id,
            }

            print(f"Processing order completion for order ID: {order.id}")
            return self.completeTransaction(complete_data)

        except Exception as e:
            error_msg = f"Error in transaction: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return Response({"message": error_msg}, status=206)

    def put(self, request):
        data = request.data["payload"]
        serializer = RecordPaymentSerializer(data=data)
        if serializer.is_valid():
            pay_type = serializer.data["pay_type"]
            pay_data = serializer.data["pay_response"]
            pay_data["user"] = request.user.id
            pay_data["organization"] = request.user.organization.id
            try:
                obj = getattr(self, pay_type)
                return obj(pay_data)
            except Exception as e:
                print(str(e))
                return Response({"error": str(e)}, status=206)
        return Response(
            {"message": "There is some Validation error", "errors": serializer.errors},
            status=206,
        )

    def initiated(self, data):
        serializer = PaymentTransactionsSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"data": serializer.data, "message": "Transaction Update Successfully"},
                status=200,
            )
        return Response(
            {"message": "There is some Validation error", "errors": serializer.errors},
            status=206,
        )

    def success(self, data):
        trans_obj = PaymentGatewayTransactions.objects.get(id=data["id"])
        ser = PaymentTransactionsSerializer(instance=trans_obj, data=data)
        if ser.is_valid():
            ser.save()
            return Response(
                {"data": ser.data, "message": "Transaction Update Successfully"},
                status=200,
            )
        return Response(
            {"message": "There is some Validation error", "error_data": ser.errors},
            status=206,
        )

    def failed(self, data):
        trans_obj = PaymentGatewayTransactions.objects.get(id=data["id"])
        ser = PaymentTransactionsSerializer(instance=trans_obj, data=data)
        if ser.is_valid():
            ser.save()
            order_id = ser.data["order_id"]
            order = Order.objects.filter(online_order_id=order_id).first()
            if order:
                order.updated_by = self.request.user.id
                order.order_status = TransactionEnum.failed.name
                order.save()
            return Response(
                {"data": ser.data, "message": "Transaction Update Successfully"},
                status=200,
            )
        return Response(
            {"message": "There is some Validation error", "error_data": ser.errors},
            status=206,
        )


class SubscriptionPaymentViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CommonSerializer
    renderer_classes = (UnpodJSONRenderer,)

    def checkSubscription(self, request):
        product_id = request.headers.get("Product-Id")
        user = request.user
        active_subscription = getActiveSubscription(user, product_id=product_id)

        if active_subscription:
            return Response({"data": {"is_subscribed": True}}, status=200)
        else:
            return Response({"message": "User is not subscribed."}, status=206)

    def subscription_detail(self, request):
        # Retrieve the active subscription for the user
        try:
            product_id = request.headers.get("Product-Id")
            domain_handle = self.request.headers.get("Org-Handle", None)
            organization = get_organization_by_domain_handle(domain_handle)

            if not organization:
                return Response({"message": "Invalid organization handle."}, status=206)

            active_subscription = getActiveSubscription(
                request.user, org_id=organization.id, product_id=product_id
            )
        except Exception as ex:
            raise APIException206(detail={"message": str(ex)})

        # If no active subscription exists, return all zeros
        if not active_subscription:
            return Response(
                {
                    "status_code": 200,
                    "message": "No active subscription found",
                    "data": {
                        "is_subscribed": False,
                        "subscription_data": {
                            "id": None,
                            "plan_name": "none",
                            "title": "No Active Plan",
                            "description": "No active subscription plan",
                            "price": 0.0,
                            "type": "none",
                            "is_active": False,
                            "start_date": None,
                            "end_date": None,
                            "product_id": None,
                            "consumption_data": {},
                        },
                    },
                },
                status=200,
            )

        # Serialize the active subscription details
        serializer = ActiveSubscriptionDetailSerializer(active_subscription)

        response_data = {
            "status_code": 200,
            "message": "Subscription details fetched successfully",
            "data": {
                "is_subscribed": True,
                "subscription_data": serializer.data,
            },
        }

        return Response(response_data, status=200)

    def createsubscription(self, request):
        domain_handle = self.request.headers.get("Org-Handle", None)
        organization = get_organization_by_domain_handle(domain_handle)

        if not organization:
            return Response({"message": "Invalid organization handle."}, status=206)

        required_fields = ["subscription_id"]
        validation = Validation(required_fields, request.data, {"notes": dict()})

        if not validation.check_required_fields():
            return Response({"errors": validation.get_error()}, status=206)

        validation.setData()
        input_data = validation.get_data()
        subscription_id = input_data.get("subscription_id")

        try:
            subscription = Subscription.objects.get(id=subscription_id, is_active=True)
        except Subscription.DoesNotExist:
            return Response(
                {"message": "Invalid or inactive subscription ID"}, status=206
            )
        product_id = request.headers.get("Product-Id")
        active_subscription = checkActiveSubscription(
            org_id=organization.id, product_id=product_id
        )

        price = float(subscription.price)
        discount = float(subscription.discount)
        final_price = price - discount if discount < price else 0.0

        if active_subscription:
            subscription_details = active_subscription.subscription_metadata.get(
                "subscription_details", {}
            )
            current_sub_id = subscription_details.get("id")
            current_sub_name = subscription_details.get("name")
            current_sub_price = subscription_details.get("price")
            current_sub_final_price = subscription_details.get(
                "final_price", current_sub_price
            )

            if current_sub_id == subscription.id:
                return Response({"message": "You are already subscribed to this plan."})
            if current_sub_final_price > final_price:
                return Response(
                    {
                        "message": complete_message(
                            ACTIVE_HIGHER_ERROR,
                            sub_name=current_sub_name,
                        )
                    },
                    status=206,
                )

        if final_price == 0:
            active_subscription = self.create_active_subscription(subscription)
            expire_active_subscription(active_subscription)

            return Response(
                {
                    "data": ActiveSubscriptionDetailSerializer(
                        active_subscription
                    ).data,
                    "message": f"{subscription.name} plan activated successfully",
                }
            )
        currency = subscription.currency
        if subscription.currency != "INR":
            currency = "INR"
            final_price = convertCurrency(final_price, subscription.currency)

        input_data["amount"] = final_price
        input_data["currency"] = currency
        input_data["order_type"] = "subscription"
        ser = OrderModelSerializer(data=input_data, context={"request": request})

        if ser.is_valid(raise_exception=True):
            order_obj = ser.save()

            razorpay_obj = create_payment_order(order_obj)
            order_obj.online_order_id = razorpay_obj["id"]
            subscription_info = get_subscription_info(subscription)

            order_obj.order_metadata = {
                "subscription_id": subscription.id,
                "offer_id": razorpay_obj["offer_id"],
                "online_order_id": order_obj.online_order_id,
                "subscription_details": subscription_info,
            }
            order_obj.save()

            return Response(razorpay_obj, status=200)

    def complete_subscription(self, request):
        data = request.data["payload"]
        serializer = VerifyPaymentSerializer(data=data)

        if serializer.is_valid():
            try:
                ser_data = serializer.data
                order_id = ser_data["payment_response"]["razorpay_order_id"]
                payment_id = ser_data["payment_response"]["razorpay_payment_id"]
                razorpay_signature = ser_data["payment_response"]["razorpay_signature"]
                razorpay_amount = ser_data["amount"]
                razorpay_currency = ser_data["currency"]
                signature = unpodRazorPay.verifySignature(
                    payment_id, order_id, razorpay_signature
                )
            except Exception as e:
                print(str(e))
                return Response({"message": str(e)}, status=206)

            payment = unpodRazorPay.client.payment.fetch(payment_id)
        else:
            return Response(
                {
                    "errors": serializer.errors,
                    "message": "There is some Validation error",
                },
                status=206,
            )
        if payment and signature:
            if payment["status"] == "authorized":
                unpodRazorPay.razorpayCapture(
                    payment_id, razorpay_amount, razorpay_currency
                )
                order_data = Order.objects.filter(online_order_id=order_id).first()
                if order_data is None:
                    return Response(
                        {"message": "Order not found for the given order ID"},
                        status=404,
                    )

                return self.complete_subscription_transaction(order_data)
            else:
                return Response({"message": "Payment Not Completed"}, status=206)
        else:
            return Response({"message": "Your Payment Not Verified Yet"}, status=206)

    def complete_subscription_transaction(self, order_data):
        if order_data.order_status == "processed":
            return Response(
                {"message": "This order has already been processed."}, status=206
            )

        # Retrieve the subscription ID from order metadata
        subscription_id = order_data.order_metadata.get("subscription_id", None)
        if not subscription_id:
            return Response(
                {"message": "No subscription ID found in order metadata."}, status=206
            )

        # Find the subscription based on the subscription ID
        subscription = Subscription.objects.filter(
            id=subscription_id, is_active=True
        ).first()

        if not subscription:
            return Response(
                {"message": "Invalid or inactive subscription ID."}, status=206
            )

        # Create an active subscription
        new_subscription = self.create_active_subscription(
            subscription, order=order_data
        )

        if new_subscription:
            # Update order status success
            order_data.order_status = "success"
            order_data.save()

            # Add subscription modules if available
            modules = get_subscription_modules(subscription)

            # Prepare the complete response
            return Response(
                {
                    "message": "Your payment is confirmed & subscription created successfully.",
                    "data": {
                        "order_id": order_data.id,
                        # "order_metadata": order_metadata,
                        "modules": modules,
                    },
                },
                status=200,
            )

        return Response(
            {"message": "Failed to create active subscription."}, status=206
        )

    def create_active_subscription(self, subscription, order=None):
        metadata = {}
        if order:
            order_metadata = order.order_metadata
            # remove subscription_details from order_metadata to avoid redundancy
            order_metadata.pop("subscription_details", None)

            metadata = {
                "order": {
                    "order_id": order.id,
                    **order_metadata,
                }
            }

        subscription_metadata = prepare_subscription_metadata(subscription)
        metadata.update(subscription_metadata)

        new_subscription = createActiveSubscription(
            subscription,
            self.request.user,
            organization=self.request.user.organization,
            order=order,
            metadata=metadata,
        )

        # Add credits if the subscription includes a Credit module
        credits_dict = metadata.get("modules", {}).get("Credit", {})

        if credits_dict:
            currency = credits_dict.pop("unit", "INR")
            amount = credits_dict.pop("quantity", "0").replace(",", "").replace(" ", "")

            currency = currency.upper()
            bits, unit_value = calculateBit(amount, currency)
            wallet = getWallet(self.request.user)
            wallet.add_credits(
                int(bits),
                unit_value,
                BitsTransactionType.added.name,
                BitsTransactionVia.recharge.name,
                self.request.user,
                currency,
            )
        return new_subscription

    def pay_invoice(self, request):
        invoice_number = self.request.data.get("invoice_number")
        if not invoice_number:
            return Response({"message": "Invoice number is required."}, status=206)

        invoice = SubscriptionInvoice.objects.get(invoice_number=invoice_number)
        if not invoice:
            return Response({"message": "Invoice not found."}, status=206)

        if invoice.status != "pending":
            return Response({"message": "Invoice is not pending."}, status=206)

        price = float(invoice.amount or 0)
        currency = invoice.currency or "INR"

        if price == 0:
            return Response(
                {"message": "Invoice amount is zero, no payment needed."}, status=206
            )

        if invoice.currency != "INR":
            currency = "INR"
            price = convertCurrency(price, invoice.currency)

        description = f"Payment for Invoice #{invoice.id}"
        order_data = {
            "amount": price,
            "currency": currency,
            "notes": [description],
            "order_type": "subscription",
        }

        ser = OrderModelSerializer(data=order_data, context={"request": request})

        if ser.is_valid(raise_exception=True):
            order_obj = ser.save()

            try:
                razorpay_obj = create_payment_order(order_obj)
                order_obj.online_order_id = razorpay_obj["id"]
                razorpay_obj["description"] = description

                # Attach invoice ID to order metadata for future reference
                order_obj.order_metadata = {
                    "invoice_id": invoice.id,
                    "offer_id": razorpay_obj["offer_id"],
                    "online_order_id": order_obj.online_order_id,
                }
                order_obj.save()

                return Response(razorpay_obj, status=200)
            except Exception as e:
                notes = order_obj.notes or []
                notes.append(f" | Error creating payment order: {str(e)}")
                order_obj.order_status = TransactionEnum.failed.name
                order_obj.notes = notes
                order_obj.save()

                return Response(
                    {"message": "Error creating payment order", "error": str(e)},
                    status=206,
                )

        return Response(
            {"message": "There is some Validation errors", "errors": ser.errors},
            status=206,
        )

    def complete_invoice_payment(self, request):
        serializer = VerifyPaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "message": "There is some Validation error",
                    "errors": serializer.errors,
                },
                status=206,
            )

        try:
            ser_data = serializer.data
            online_order_id = ser_data["payment_response"]["razorpay_order_id"]
            payment_id = ser_data["payment_response"]["razorpay_payment_id"]
            razorpay_signature = ser_data["payment_response"]["razorpay_signature"]
            razorpay_amount = ser_data["amount"]
            razorpay_currency = ser_data["currency"]
            signature = unpodRazorPay.verifySignature(
                payment_id, online_order_id, razorpay_signature
            )
        except Exception as e:
            print(str(e))
            return Response({"message": str(e)}, status=206)

        payment = unpodRazorPay.client.payment.fetch(payment_id)

        if payment and signature:
            if payment["status"] == "authorized":
                unpodRazorPay.razorpayCapture(
                    payment_id, razorpay_amount, razorpay_currency
                )
                order_data = Order.objects.filter(
                    online_order_id=online_order_id
                ).first()
                if order_data is None:
                    return Response(
                        {"message": "Order not found for the given order ID"},
                        status=404,
                    )

                # Retrieve the invoice ID from order metadata
                invoice_id = order_data.order_metadata.get("invoice_id", None)
                invoice = SubscriptionInvoice.objects.get(id=invoice_id)
                if not invoice:
                    return Response({"message": "Invoice not found."}, status=206)

                invoice.status = "paid"
                invoice.payment_at = get_datetime_now()
                invoice.order = order_data
                invoice.save()

                order_data.order_status = "success"
                order_data.save()

                # Prepare the complete response
                return Response(
                    {
                        "message": "Your payment is confirmed & invoice paid successfully.",
                        "data": {
                            "order_id": order_data.id,
                            "invoice_id": invoice.id,
                        },
                    },
                    status=200,
                )
            else:
                return Response({"message": "Payment Not Completed"}, status=206)
        else:
            return Response({"message": "Your Payment Not Verified Yet"}, status=206)

    def create_addon_subscription(self, request):
        try:
            domain_handle = self.request.headers.get("Org-Handle", None)
            product_id = request.headers.get("Product-Id")
            organization = get_organization_by_domain_handle(domain_handle)

            if not organization:
                return Response(
                    {
                        "message": "Organization not found for the given domain handle",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            required_fields = ["currency", "addons"]
            validation = Validation(required_fields, request.data, {"notes": dict()})
            if not validation.check_required_fields():
                return Response({"errors": validation.get_error()}, status=206)

            validation.setData()
            input_data = validation.get_data()
            addons = input_data.get("addons", [])
            request_currency = input_data.get("currency")
            price = float(0)

            serializer = AddOnSubscribeItemSerializer(data=addons, many=True)
            serializer.is_valid(raise_exception=True)

            actSubscription = ActiveSubscription.objects.filter(
                organization=organization,
                is_active=True,
                expired=False,
                product_id=product_id,
            ).first()

            subscription_details = actSubscription.subscription_metadata.get(
                "subscription_details", {}
            )
            subscription_id = subscription_details.get("id")
            modules = actSubscription.subscription_metadata.get("modules", {})

            modules_data = []
            for name, module in modules.items():
                module["name"] = name
                modules_data.append(module)

            added_modules = {}

            for item in serializer.validated_data:
                quantity = int(item.get("quantity"))
                codename = item.get("codename")
                module = find_by_codename(modules_data, codename)
                module_id = module.get("module_id")
                module_name = module.get("name")
                display_name = module.get("display_name")
                is_unlimited = module.get("is_unlimited")
                price_type = module.get("price_type")
                cost = module.get("cost")
                unit = module.get("unit")
                tax_percentage = extract_number(module.get("tax_percentage"))
                tax_code = module.get("tax_code")
                include_in_billing = module.get("include_in_billing", True)

                if is_unlimited or price_type == "fixed":
                    item_amount = cost
                else:
                    item_amount = cost * quantity

                tax_amount = round(((item_amount * tax_percentage) / 100), 2)
                total_amount = item_amount + tax_amount
                price += total_amount

                module_data = {
                    "module_id": module_id,
                    "codename": codename,
                    "display_name": display_name,
                    "is_unlimited": is_unlimited,
                    "quantity": quantity,
                    "price_type": price_type,
                    "cost": cost,
                    "unit": unit,
                    "tax_percentage": tax_percentage,
                    "tax_code": tax_code,
                    "amount": item_amount,
                    "tax_amount": tax_amount,
                    "total_amount": total_amount,
                    "include_in_billing": include_in_billing,
                }

                added_modules[module_name] = module_data

            if price == 0:
                return Response(
                    {
                        "message": "Add-on subscription amount is zero, no payment needed."
                    },
                    status=206,
                )

            currency = request_currency or "INR"
            if request_currency != "INR":
                currency = "INR"
                price = convertCurrency(price, request_currency)

            description = f"Payment for Add-on Subscription"
            order_data = {
                "amount": price,
                "currency": currency,
                "notes": [description],
                "order_type": "addon_subscription",
            }

            ser = OrderModelSerializer(data=order_data, context={"request": request})
            ser.is_valid(raise_exception=True)

            if ser.is_valid(raise_exception=True):
                order_obj = ser.save()

                razorpay_obj = create_payment_order(order_obj)
                order_obj.online_order_id = razorpay_obj["id"]
                razorpay_obj["description"] = description

                order_obj.order_metadata = {
                    "subscription_id": subscription_id,
                    "offer_id": razorpay_obj["offer_id"],
                    "online_order_id": order_obj.online_order_id,
                    "modules": added_modules,
                }
                order_obj.save()

                return Response(razorpay_obj, status=200)

            return Response(
                {
                    "message": "There is some Validation errors",
                    "errors": ser.errors,
                    "price": price,
                    "added_modules": added_modules,
                },
                status=206,
            )
        except serializers.ValidationError as e:
            return Response(
                {
                    "message": e.args[0] if hasattr(e, "args") and e.args else str(e),
                },
                status=status.HTTP_206_PARTIAL_CONTENT,
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {
                    "message": "An error occurred while creating add-on subscription.",
                    "error": str(e),
                },
                status=206,
            )

    def complete_addon_subscription(self, request):
        try:
            domain_handle = self.request.headers.get("Org-Handle", None)
            product_id = request.headers.get("Product-Id")
            organization = get_organization_by_domain_handle(domain_handle)

            if not organization:
                return Response(
                    {
                        "message": "Organization not found for the given domain handle",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = VerifyPaymentSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {
                        "message": "There is some Validation error",
                        "errors": serializer.errors,
                    },
                    status=206,
                )

            ser_data = serializer.data
            online_order_id = ser_data["payment_response"]["razorpay_order_id"]
            payment_id = ser_data["payment_response"]["razorpay_payment_id"]
            razorpay_signature = ser_data["payment_response"]["razorpay_signature"]
            razorpay_amount = ser_data["amount"]
            razorpay_currency = ser_data["currency"]
            signature = unpodRazorPay.verifySignature(
                payment_id, online_order_id, razorpay_signature
            )

            payment = unpodRazorPay.client.payment.fetch(payment_id)

            if payment and signature:
                if payment["status"] == "authorized":
                    unpodRazorPay.razorpayCapture(
                        payment_id, razorpay_amount, razorpay_currency
                    )
                    order_data = Order.objects.filter(
                        online_order_id=online_order_id
                    ).first()
                    if order_data is None:
                        return Response(
                            {"message": "Order not found for the given order ID"},
                            status=404,
                        )

                    actSubscription = ActiveSubscription.objects.filter(
                        organization=organization,
                        is_active=True,
                        expired=False,
                        product_id=product_id,
                    ).first()

                    # Retrieve the subscription add-on modules from order metadata
                    modules = order_data.order_metadata.get("modules", {})
                    assign_addons_to_subscription(modules, actSubscription, order_data)

                    order_data.order_status = "success"
                    order_data.save()

                    # Prepare the complete response
                    return Response(
                        {
                            "message": "Your payment is confirmed & add-on subscription created successfully.",
                            "data": {
                                "order_id": order_data.id,
                                "modules": modules,
                            },
                        },
                        status=200,
                    )
                else:
                    return Response({"message": "Payment Not Completed"}, status=206)
            else:
                return Response(
                    {"message": "Your Payment Not Verified Yet"}, status=206
                )

        except serializers.ValidationError as e:
            return Response(
                {
                    "message": e.args[0] if hasattr(e, "args") and e.args else str(e),
                },
                status=status.HTTP_206_PARTIAL_CONTENT,
            )

        except Exception as e:
            traceback.print_exc()
            return Response(
                {
                    "message": "An error occurred while creating add-on subscription.",
                    "error": str(e),
                },
                status=206,
            )

    def subscription_test(self, request):
        product_id = request.headers.get("Product-Id")
        user = request.user
        subscription = Subscription.objects.filter(id=6, is_active=True).first()

        metadata = prepare_subscription_metadata(subscription)
        subscription_data = metadata.get("subscription_data")

        print("Metadata subscription_data :", metadata.get("subscription_data"))
        consumption_data = []

        for module_name, module_data in subscription_data.get("modules").items():
            print(
                f"*******************module_name={module_name}: module_data={module_data} ========================="
            )
            consumption_data.append(
                {
                    "feature": module_name,
                    "allocated": module_data.get("quantity", 0),
                    "consumed": 0,
                    "unit": module_data.get("unit", ""),
                    "warning_threshold": 80,
                    "reset_date": timezone.now() + timezone.timedelta(days=30),
                }
            )

        print("======================================")

        print("Final Metadata :", consumption_data)

        if metadata:
            return Response({"data": consumption_data}, status=200)
        else:
            return Response({"message": "User is not subscribed."}, status=206)

    def complete_subscription_demo(self, request):
        product_id = request.headers.get("Product-Id")
        user = request.user
        order_id = request.data.get("order_id")

        # active_subscription = ActiveSubscription.objects.filter(
        #     pk=3, is_active=True
        # ).first()
        #
        # serializer = ActiveSubscriptionDetailSerializer(active_subscription)

        order_data = Order.objects.filter(online_order_id=order_id).first()

        # Retrieve the subscription ID from order metadata
        subscription_id = order_data.order_metadata.get("subscription_id")
        if not subscription_id:
            return Response(
                {"message": "No subscription ID found in order metadata."}, status=206
            )

        # Find the subscription based on the subscription ID
        subscription = Subscription.objects.filter(
            id=subscription_id, is_active=True
        ).first()

        metadata = {}
        if order_data:
            metadata = {
                "order_id": order_data.id,
                "order_metadata": order_data.order_metadata,
            }
        subscription_metadata = prepare_subscription_metadata(subscription)
        metadata.update(subscription_metadata)

        active_subscription = createActiveSubscription(
            subscription,
            self.request.user,
            organization=self.request.user.organization,
            metadata=metadata,
        )

        serializer = ActiveSubscriptionDetailSerializer(active_subscription)

        # Retrieve the order using the order_id
        # order_data = Order.objects.filter(id=order_id).first()

        # Check if order_data exists
        # if not order_data:
        #     return Response({"error": "Order not found"}, status=404)
        #
        # order_data.save()

        # return self.complete_subscription_transaction(order_data)

        return Response(
            {
                "message": "Your payment is confirmed & subscription created successfully.",
                "data": {
                    "active_subscription": serializer.data,
                    "product_id": product_id,
                    "user": user.username,
                },
            },
            status=200,
        )

    def cancel_subscription(self, request):
        product_id = request.headers.get("Product-Id")
        user = request.user
        active_subscription = getActiveSubscription(user, product_id=product_id)

        if not active_subscription:
            return Response({"message": "No active subscription found."}, status=206)

        active_subscription.is_active = False
        active_subscription.save()

        # Fetch the basic subscription plan
        basic_subscription = Subscription.objects.filter(name="basic").first()

        if not basic_subscription:
            return Response(
                {"message": "Basic subscription plan not found."}, status=206
            )

        new_subscription = self.create_active_subscription(basic_subscription)

        # Prepare order metadata
        subscription_info = get_subscription_info(basic_subscription)
        metadata = {
            "subscription_id": basic_subscription.id,
            "subscription_name": basic_subscription.name,
            "subscription_details": subscription_info,
            # "subscription_details": {
            #     "name": basic_subscription.name,
            #     "price": str(basic_subscription.price),
            #     "is_custom": basic_subscription.is_custom,
            #     "description": basic_subscription.description,
            # },
            "subscription_data": {"modules": {}},
        }

        subscription_modules = basic_subscription.subscriptionmodules_subscription.all()
        for module in subscription_modules:
            if module.module:
                module_name = module.module.name
                module_data = {"unit": module.module.unit, "quantity": module.quantity}
                # Add the module data to the subscription_data
                metadata["subscription_data"]["modules"][module_name] = module_data
            else:
                print(
                    f"Warning: Module for {module} is None"
                )  # Log a warning for debugging

        response_data = {
            "message": "Subscription cancelled and basic plan activated.",
            "order_metadata": new_subscription.subscription_metadata,
            "metadata": metadata,
        }

        return Response(response_data, status=200)
