import razorpay
from django.conf import settings
import hmac
import hashlib
import requests

from unpod.wallet.models import PaymentGatewayCustomer


def getRazorPayClient():
    RAZORPAY_KEY = settings.RAZORPAY_KEY
    RAZORPAY_SECERT = settings.RAZORPAY_SECERT
    client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECERT))
    client.set_app_details({"title": "Unpod App", "version": "1.0.1"})
    return client


class UnpodRazorPay:
    client: razorpay.Client = None

    def __init__(self) -> None:
        if not self.client:
            self.client = getRazorPayClient()

    # Capturing the Payment after authorisation of signature of the payment Response. For More Refer to the Razorpay Doc
    def razorpayCapture(self, payment_id, amount, payment_currency):
        try:
            # First, fetch the payment details to see the authorized amount
            print(f"\n=== DEBUG: Fetching payment details for ID: {payment_id} ===")
            payment = self.client.payment.fetch(payment_id)
            print(f"Payment details: {payment}")
            print(
                f"Amount authorized: {payment.get('amount')} {payment.get('currency')}"
            )
            print(f"Payment status: {payment.get('status')}")
            print(f"Order ID: {payment.get('order_id')}")
            print("=========================================\n")

            # Get the authorized amount from Razorpay
            authorized_amount = payment.get("amount", 0)

            # Convert input amount to paise for comparison
            if isinstance(amount, float) and amount != int(amount):
                amount_in_paise = int(round(amount * 100))
            else:
                amount_in_paise = int(amount)

            # Always use the authorized amount from Razorpay to avoid mismatches
            capture_amount = authorized_amount
            print(
                f"Using authorized amount for capture: {capture_amount} {payment_currency}"
            )

            # Proceed with capture using the authorized amount
            print(f"Attempting to capture {capture_amount} {payment_currency}...")
            resp = self.client.payment.capture(
                payment_id, capture_amount, {"currency": payment_currency}
            )
            print(f"Capture successful - {resp}")
            return resp

        except Exception as e:
            print(f"Error in razorpayCapture: {str(e)}")
            if "payment" in locals():
                print(f"Payment status: {payment.get('status')}")
                print(
                    f"Payment amount: {payment.get('amount')} {payment.get('currency')}"
                )
            raise

    def createRazorPayOrder(self, data):
        orderData = {**data}
        payment = self.client.order.create(data=orderData)
        return payment

    def genrateSignature(self, payment_id, order_id):
        secret_key = bytes(settings.RAZORPAY_SECERT, "utf-8")
        total_params = (order_id + "|" + payment_id).encode()
        signature = hmac.new(secret_key, total_params, hashlib.sha256).hexdigest()
        return "{0}".format(signature)

    def verifySignature(self, payment_id, order_id, razorpay_signature):
        generated_signature = self.genrateSignature(payment_id, order_id)
        return generated_signature == razorpay_signature

    def genrateSubscriptionSignature(self, payment_id, subscription_id):
        secret_key = bytes(settings.RAZORPAY_SECERT, "utf-8")
        total_params = (payment_id + "|" + subscription_id).encode()
        signature = hmac.new(secret_key, total_params, hashlib.sha256).hexdigest()
        return "{0}".format(signature)

    def verifySubsciptionSignature(
        self, payment_id, subscription_id, razorpay_signature
    ):
        generated_signature = self.genrateSubscriptionSignature(
            payment_id, subscription_id
        )
        return generated_signature == razorpay_signature

    def getCheckCustomer(self, user):
        customer, created = PaymentGatewayCustomer.objects.get_or_create(
            user=user, payment_mode="razorpay"
        )
        if customer.customer_id:
            return customer
        else:
            customer_data = {}
            customer_data["email"] = user.email
            customer_data["name"] = user.full_name
            customer_data["contact"] = user.phone_number
            customer_res = self.createCustomer(customer_data)
            if "id" in customer_res:
                customer.customer_id = customer_res["id"]
                customer.customer_data = customer_data
                customer.save()
                customer.refresh_from_db()
            return customer

    def createCustomer(self, customer_info):
        customer_info["fail_existing"] = "0"
        res = self.client.customer.create(customer_info)
        return res

    def createRecurringOrder(self, customer_id, orderObj):
        recurringOrderData = {
            "currency": "INR",
            "method": "upi",
            "token": {"max_amount": 200000, "frequency": "as_presented"},
            "payment_capture": 0,
        }
        recurringOrderData["customer_id"] = customer_id
        recurringOrderData["amount"] = orderObj.amount * 100
        recurringOrderData["notes"] = {"base_amount": orderObj.amount}
        recurringOrderData["receipt"] = orderObj.order_number
        res = self.client.order.create(recurringOrderData)
        return res

    def validateVpa(self, upi_id):
        url = "https://api.razorpay.com/v1/payments/validate/vpa"
        body = {"vpa": upi_id}
        RAZORPAY_KEY = "rzp_test_y6dtiSmMIHTUfd"
        RAZORPAY_SECERT = "TI5S3BPb4EUcuR98v8rxW338"
        res = requests.post(url, json=body, auth=(RAZORPAY_KEY, RAZORPAY_SECERT))
        if res.status_code == 200:
            return {"data": res.json(), "success": True}, 200
        res_data = res.json()
        return {
            "data": {**res_data.get("error", {}), "success": False},
            "success": False,
        }, 206

    def validateIfsc(self, ifsc):
        ifsc = ifsc.upper()
        url = f"https://ifsc.razorpay.com/{ifsc}"
        res = requests.get(url)
        if res.status_code == 200:
            return {"data": res.json(), "success": True}, 200
        res_text = res.json()
        return {
            "message": res_text,
            "error": "Invalid IFSC Code",
            "success": False,
        }, 206


unpodRazorPay = UnpodRazorPay()
