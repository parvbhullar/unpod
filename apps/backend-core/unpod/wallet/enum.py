from unpod.common.mixin import ChoiceEnum


class BitsTransactionType(ChoiceEnum):
    pending = "Pending"
    added = "Added"
    subtracted = "Subtracted"
    hold = "Hold"
    cancelled = "Cancelled"


class BitsTransactionVia(ChoiceEnum):
    recharge = "Recharge"
    earn = "Earn"
    spent = "Spent"
    joining_bonus = "Joining Bonus"
    referral_bonus = "Referral Bonus"
    gifted = "Gifted"
    transferred = "Transferred"
    returned = "Returned"
    order_fee = "Order Fee"


class CurrencyEnum(ChoiceEnum):
    INR = "INR"
    USD = "USD"
    BITS = "BITS"


class TransactionEnum(ChoiceEnum):
    created = "Created"
    initiated = "Initiated"
    success = "Success"
    failed = "Failed"


class PaymentMethodEnum(ChoiceEnum):
    razorpay = "Razorpay"


class SubscriptionTypes(ChoiceEnum):
    standard = "Standard"
    contact = "Contact"


class ChargeTypes(ChoiceEnum):
    subscription = "Subscription"
    addon_subscription = "Add-on Subscription"
    credits = "Credits"
