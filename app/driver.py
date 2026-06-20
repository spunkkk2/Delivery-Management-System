# app/driver.py

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from . import db

from .decorators import (
    role_required,
    current_user
)

from .models import (
    User,
    Order,
    DriverLedger
)

from .services import (
    log_activity
)

from .accounting import (
    apply_delivery_accounting
)

driver_bp = Blueprint(
    "driver",
    __name__,
    url_prefix="/driver"
)


##################################################
# DASHBOARD
##################################################

@driver_bp.route("/")
@role_required("driver")
def dashboard():

    driver = current_user()

    active_orders = Order.query.filter(
        Order.driver_id == driver.id,
        Order.status.in_(
            [
                "Assigned",
                "Accepted",
                "Picked Up"
            ]
        )
    ).order_by(
        Order.id.desc()
    ).all()

    completed_orders = Order.query.filter(
        Order.driver_id == driver.id,
        Order.status == "Delivered"
    ).count()

    declined_orders = Order.query.filter(
        Order.driver_id == driver.id,
        Order.status == "Declined"
    ).count()

    active_count = len(
        active_orders
    )

    total_decisions = (
        completed_orders +
        declined_orders
    )

    acceptance_rate = 100

    if total_decisions > 0:

        acceptance_rate = round(
            (
                completed_orders /
                total_decisions
            ) * 100,
            2
        )

    history = Order.query.filter(
        Order.driver_id == driver.id
    ).order_by(
        Order.id.desc()
    ).limit(100).all()

    ledger = (
        DriverLedger.query.filter(
            DriverLedger.driver_id == driver.id
        )
            .order_by(
            DriverLedger.id.desc()
        )
            .limit(100)
            .all()
    )

    total_earnings = 0

    for item in ledger:

        if item.amount > 0:
            total_earnings += item.amount

    return render_template(
        "driver/dashboard.html",

        user=driver,

        active_orders=active_orders,

        history=history,

        ledger=ledger,

        completed_orders=completed_orders,

        declined_orders=declined_orders,

        active_count=active_count,

        acceptance_rate=acceptance_rate,

        total_earnings=round(
            total_earnings,
            2
        )
    )


##################################################
# CHANGE STATUS
##################################################

@driver_bp.route(
    "/status",
    methods=["POST"]
)
@role_required("driver")
def change_status():

    driver = current_user()

    status = request.form[
        "status"
    ]

    allowed = [
        "Available",
        "Busy",
        "Offline"
    ]

    if status not in allowed:

        flash(
            "Invalid status"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    driver.status = status

    db.session.commit()

    log_activity(
        driver.username,
        f"Driver Status Changed To {status}"
    )

    return redirect(
        url_for(
            "driver.dashboard"
        )
    )


##################################################
# ACCEPT ORDER
##################################################

@driver_bp.route(
    "/orders/<int:order_id>/accept"
)
@role_required("driver")
def accept_order(order_id):

    driver = current_user()

    order = Order.query.get_or_404(
        order_id
    )

    if order.driver_id != driver.id:

        flash(
            "Not your order"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    if order.status != "Assigned":

        flash(
            "Order cannot be accepted"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    order.status = "Accepted"

    db.session.commit()

    log_activity(
        driver.username,
        f"Accept Order #{order.id}"
    )

    return redirect(
        url_for(
            "driver.dashboard"
        )
    )


##################################################
# DECLINE ORDER
##################################################

@driver_bp.route(
    "/orders/<int:order_id>/decline",
    methods=["POST"]
)
@role_required("driver")
def decline_order(order_id):

    driver = current_user()

    order = Order.query.get_or_404(
        order_id
    )

    if order.driver_id != driver.id:

        flash(
            "Not your order"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    if order.status != "Assigned":

        flash(
            "Order cannot be declined"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    reason = request.form.get(
        "reason",
        ""
    )

    order.status = "Declined"

    order.decline_reason = reason

    db.session.commit()

    log_activity(
        driver.username,
        f"Decline Order #{order.id}"
    )

    return redirect(
        url_for(
            "driver.dashboard"
        )
    )


##################################################
# PICKED UP
##################################################

@driver_bp.route(
    "/orders/<int:order_id>/pickup"
)
@role_required("driver")
def pickup_order(order_id):

    driver = current_user()

    order = Order.query.get_or_404(
        order_id
    )

    if order.driver_id != driver.id:

        flash(
            "Not your order"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    if order.status != "Accepted":

        flash(
            "Order cannot be picked up"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    order.status = "Picked Up"

    db.session.commit()

    log_activity(
        driver.username,
        f"Picked Up Order #{order.id}"
    )

    return redirect(
        url_for(
            "driver.dashboard"
        )
    )


##################################################
# DELIVERED
##################################################

@driver_bp.route(
    "/orders/<int:order_id>/deliver"
)
@role_required("driver")
def deliver_order(order_id):

    driver = current_user()

    order = Order.query.get_or_404(
        order_id
    )

    if order.driver_id != driver.id:

        flash(
            "Not your order"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    if order.status != "Picked Up":

        flash(
            "Order cannot be delivered"
        )

        return redirect(
            url_for(
                "driver.dashboard"
            )
        )

    order.status = "Delivered"

    db.session.commit()

    apply_delivery_accounting(
        order
    )

    log_activity(
        driver.username,
        f"Delivered Order #{order.id}"
    )

    return redirect(
        url_for(
            "driver.dashboard"
        )
    )


##################################################
# DELIVERY HISTORY
##################################################

@driver_bp.route("/history")
@role_required("driver")
def history():

    driver = current_user()

    orders = Order.query.filter(
        Order.driver_id == driver.id
    ).order_by(
        Order.id.desc()
    ).all()

    return render_template(
        "driver/history.html",
        orders=orders,
        user=driver
    )


##################################################
# LEDGER
##################################################

@driver_bp.route("/ledger")
@role_required("driver")
def ledger():

    driver = current_user()

    entries = DriverLedger.query.filter(
        DriverLedger.driver_id == driver.id
    ).order_by(
        DriverLedger.id.desc()
    ).all()

    return render_template(
        "driver/ledger.html",
        entries=entries,
        user=driver
    )

@driver_bp.route("/accounts")
@role_required("driver")
def accounts():

    driver = current_user()

    completed_orders = Order.query.filter(
        Order.driver_id == driver.id,
        Order.status == "Delivered"
    ).count()

    declined_orders = Order.query.filter(
        Order.driver_id == driver.id,
        Order.status == "Declined"
    ).count()

    total_orders = (
        completed_orders +
        declined_orders
    )

    acceptance_rate = 100

    if total_orders > 0:

        acceptance_rate = round(
            (
                completed_orders /
                total_orders
            ) * 100,
            1
        )

    ledger_entries = (
        DriverLedger.query
        .filter(
            DriverLedger.driver_id == driver.id
        )
        .order_by(
            DriverLedger.id.desc()
        )
        .all()
    )

    return render_template(
        "driver/accounts.html",
        user=driver,
        completed_orders=completed_orders,
        declined_orders=declined_orders,
        acceptance_rate=acceptance_rate,
        ledger_entries=ledger_entries
    )