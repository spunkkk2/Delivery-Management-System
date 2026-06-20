from . import db
from .models import (
    DriverLedger
)
from .services import (
    calculate_company_share
)


def apply_delivery_accounting(
    order
):

    driver = order.driver

    if not driver:
        return

    balance_before = driver.balance

    company_share = calculate_company_share(
        order.commission,
        order.driver_commission
    )

    if order.payment_type == "Cash":

        driver.balance -= company_share

        amount = -company_share

        transaction_type = (
            "Cash Commission"
        )

    else:

        driver.balance += order.driver_commission

        amount = order.driver_commission

        transaction_type = (
            "Paid Commission"
        )

    ledger = DriverLedger(
        driver_id=driver.id,
        order_id=order.id,
        transaction_type=transaction_type,
        amount=amount,
        balance_after=driver.balance
    )

    db.session.add(ledger)

    db.session.commit()

    return {
        "before": balance_before,
        "after": driver.balance
    }