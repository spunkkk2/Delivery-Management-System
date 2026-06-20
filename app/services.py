from . import db
from .models import (
    ActivityLog,
    Setting,
    Shop
)


def get_driver_commission_ratio(
    driver=None
):

    if (
        driver is not None
        and driver.driver_commission_ratio
        is not None
    ):
        return float(
            driver.driver_commission_ratio
        )

    setting = Setting.query.first()

    if setting and setting.driver_commission_ratio is not None:
        return setting.driver_commission_ratio

    return 0.75


def calculate_driver_commission(
    commission,
    ratio=None
):

    if ratio is None:
        ratio = get_driver_commission_ratio()

    return round(
        float(commission) * ratio,
        2
    )


def sync_order_driver_commission(
    order,
    driver=None
):

    if (
        driver is None
        and order.driver_id
    ):
        driver = order.driver

    ratio = get_driver_commission_ratio(
        driver
    )

    order.driver_commission = (
        calculate_driver_commission(
            order.commission,
            ratio
        )
    )


def calculate_company_share(
    commission,
    driver_commission=None
):

    if driver_commission is None:
        driver_commission = (
            calculate_driver_commission(
                commission
            )
        )

    return round(
        float(commission) - float(driver_commission),
        2
    )


def log_activity(
    username,
    action
):

    log = ActivityLog(
        username=username,
        action=action
    )

    db.session.add(log)
    db.session.commit()


def get_or_create_shop(
    shop_name,
    phone="",
    notes=""
):

    shop = Shop.query.filter_by(
        name=shop_name.strip()
    ).first()

    if shop:
        return shop

    shop = Shop(
        name=shop_name.strip(),
        phone=phone,
        notes=notes
    )

    db.session.add(shop)
    db.session.commit()

    return shop