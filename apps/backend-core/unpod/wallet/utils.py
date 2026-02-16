from cryptography.fernet import Fernet
from django.utils import timezone


def decodeData(data):
    f = Fernet(b"7Ci1sH14V_kIvrDhsYUhik8ydxOgMl7i3dlASfNQ-Dg=")
    data = f.decrypt(bytes(data, "utf-8"))
    return data


def get_recient_number(reciept_number):
    current = timezone.now()
    current_str = current.strftime("%m-%Y")
    return f"{current_str}/{reciept_number}"


def generateRazorPayOrder(input_data, request):
    from unpod.wallet.serializers import OrderModelSerializer
    from unpod.wallet.razorpay import unpodRazorPay

    ser = OrderModelSerializer(data=input_data, context={"request": request})
    ser.is_valid(raise_exception=True)
    order_obj = ser.save()
    razorPayData = {
        "amount": order_obj.amount * 100,
        "currency": order_obj.currency,
        "notes": order_obj.notes,
        "receipt": order_obj.order_number,
        "payment_capture": 0,
        "method": "upi",
    }
    razorpay_obj = unpodRazorPay.createRazorPayOrder(razorPayData)
    order_obj.online_order_id = razorpay_obj["id"]
    order_obj.save()
    order_obj.refresh_from_db()
    return order_obj


def updateConfirmedOrder(order_id, user):
    from unpod.wallet.models import Order, TransactionEnum
    from unpod.wallet.serializers import increment_receipt_number

    order = Order.objects.filter(online_order_id=order_id).first()
    if order:
        order.updated_by = user.id
        order.order_status = TransactionEnum.success.name
        order.receipt_number = increment_receipt_number()
        order.save()
    return order


def generateRecurringRazorPayOrder(input_data, request):
    from unpod.wallet.serializers import OrderModelSerializer
    from unpod.wallet.razorpay import unpodRazorPay

    ser = OrderModelSerializer(data=input_data, context={"request": request})
    ser.is_valid(raise_exception=True)
    order_obj = ser.save()
    razorpay_customer = unpodRazorPay.getCheckCustomer(request.user)
    razorpay_obj = unpodRazorPay.createRecurringOrder(
        razorpay_customer.customer_id, order_obj
    )
    order_obj.online_order_id = razorpay_obj["id"]
    order_obj.save()
    order_obj.refresh_from_db()
    razorpay_obj["customer_id"] = razorpay_customer.customer_id
    return order_obj, razorpay_obj


def create_payment_order(order_obj):
    from unpod.wallet.razorpay import unpodRazorPay

    # Convert amount to paise for Razorpay
    amount_in_paise = int(order_obj.amount * 100)

    razorPayData = {
        "amount": amount_in_paise,
        "currency": order_obj.currency,
        "notes": order_obj.notes,
        "receipt": order_obj.receipt_number,
        "payment_capture": 0,
    }
    return unpodRazorPay.createRazorPayOrder(razorPayData)
