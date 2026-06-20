# app/operator.py

import re

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)

from werkzeug.security import (
    generate_password_hash
)

from . import db

from .decorators import (
    role_required,
    current_user
)

from .models import (
    User,
    Order,
    Shop,
    DriverLedger,
    ActivityLog,
    Setting,
    Place,
    RouteCommission
)

from .services import (
    log_activity,
    sync_order_driver_commission
)

operator_bp = Blueprint(
    "operator",
    __name__,
    url_prefix="/operator"
)


@operator_bp.before_request
def enforce_operator_permissions():

    from .permissions import (
        enforce_operator_access
    )

    return enforce_operator_access(
        current_user(),
        request.endpoint
    )


PHONE_RE = re.compile(
    r"^\d{10}$"
)


def validate_phone(
    value,
    required=False
):

    phone = (
        value or ""
    ).strip()

    if not phone:

        if required:
            return (
                None,
                "يجب أن يكون الهاتف 10 أرقام"
            )

        return "", None

    if not PHONE_RE.fullmatch(
        phone
    ):
        return (
            None,
            "يجب أن يكون الهاتف 10 أرقام"
        )

    return phone, None


##################################################
# DASHBOARD
##################################################

@operator_bp.route("/")
@role_required("operator", "admin")
def dashboard():

    pending_orders = Order.query.filter(
        Order.status == "Pending"
    ).count()

    active_orders = Order.query.filter(
        Order.status.in_(
            [
                "Assigned",
                "Accepted",
                "Picked Up"
            ]
        )
    ).count()

    completed_orders = Order.query.filter(
        Order.status == "Delivered"
    ).count()

    declined_orders = Order.query.filter(
        Order.status == "Declined"
    ).count()

    drivers = User.query.filter_by(
        role="driver",
        active=True
    ).all()

    orders = Order.query.order_by(
        Order.id.desc()
    ).limit(100).all()

    all_routes = RouteCommission.query.all()

    route_commissions = {
        f"{route.from_place_id}-{route.to_place_id}": route.commission
        for route in all_routes
    }

    return render_template(
        "operator/dashboard.html",
        user=current_user(),
        drivers=drivers,
        orders=orders,
        pending_orders=pending_orders,
        active_orders=active_orders,
        completed_orders=completed_orders,
        declined_orders=declined_orders,
        commission=Setting.query.first(),
        shops=Shop.query.order_by(
            Shop.name
        ).all(),
        places=Place.query.order_by(
            Place.name
        ).all(),
        route_commissions=route_commissions
    )


##################################################
# CREATE ORDER
##################################################

@operator_bp.route(
    "/orders/create",
    methods=["POST"]
)
@role_required("operator")
def create_order():

    shop = Shop.query.get_or_404(
        int(
            request.form["shop_id"]
        )
    )

    commission = request.form.get(
        "commission"
    )

    if not commission:

        commission = (
            Setting.query.first()
            .default_commission
        )

    amount_paid_to_shop = float(
        request.form[
            "amount_paid_to_shop"
        ]
    )

    amount_received_from_customer = (
        float(commission)
        + amount_paid_to_shop
    )

    customer_phone, phone_error = (
        validate_phone(
            request.form.get(
                "customer_phone"
            ),
            required=True
        )
    )

    if phone_error:

        flash(phone_error)

        return redirect(
            url_for(
                "operator.dashboard"
            )
        )

    order = Order(

        shop_id=shop.id,

        customer_name=request.form[
            "customer_name"
        ],

        customer_phone=customer_phone,

        destination=request.form.get(
            "delivery_location",
            ""
        ),

        notes=request.form.get(
            "notes",
            ""
        ),

        shop_location=shop.place.name
        if shop.place
        else "",

        delivery_location=request.form[
            "delivery_location"
        ],

        amount_paid_to_shop=amount_paid_to_shop,

        amount_received_from_customer=amount_received_from_customer,

        order_total=amount_paid_to_shop,

        commission=float(
            commission
        ),

        payment_type=request.form[
            "payment_type"
        ],

        destination_place_id=int(
            request.form[
                "destination_place_id"
            ]
        ),

        created_by=current_user().username,

        status="Pending"
    )

    sync_order_driver_commission(order)

    db.session.add(order)

    db.session.commit()

    log_activity(
        current_user().username,
        f"Create Order #{order.id}"
    )

    flash(
        f"تم إنشاء الطلب #{order.id}"
    )

    return redirect(
        url_for(
            "operator.dashboard"
        )
    )


##################################################
# EDIT ORDER
##################################################

@operator_bp.route(
    "/orders/<int:order_id>/edit",
    methods=["POST"]
)
@role_required("operator", "admin")
def edit_order(order_id):

    order = Order.query.get_or_404(
        order_id
    )

    shop = Shop.query.get_or_404(
        int(
            request.form["shop_id"]
        )
    )

    order.shop_id = shop.id

    order.shop_location = (
        shop.place.name
        if shop.place
        else ""
    )

    order.customer_name = (
        request.form[
            "customer_name"
        ]
    )

    customer_phone, phone_error = (
        validate_phone(
            request.form.get(
                "customer_phone"
            ),
            required=True
        )
    )

    if phone_error:

        flash(phone_error)

        return redirect(
            url_for(
                "operator.orders"
            )
        )

    order.customer_phone = (
        customer_phone
    )

    order.destination_place_id = int(
        request.form[
            "destination_place_id"
        ]
    )

    delivery_location = (
        request.form.get(
            "delivery_location",
            ""
        )
    )

    order.destination = delivery_location

    order.delivery_location = (
        delivery_location
    )

    order.notes = (
        request.form["notes"]
    )

    order.order_total = float(
        request.form["order_total"]
    )

    order.commission = float(
        request.form["commission"]
    )

    sync_order_driver_commission(order)

    order.payment_type = (
        request.form.get(
            "payment_type",
            "Cash"
        )
    )

    db.session.commit()

    log_activity(
        current_user().username,
        f"Edit Order #{order.id}"
    )

    return redirect(
        url_for(
            "operator.orders"
        )
    )


##################################################
# CANCEL ORDER
##################################################

@operator_bp.route(
    "/orders/<int:order_id>/cancel"
)
@role_required("operator", "admin")
def cancel_order(order_id):

    order = Order.query.get_or_404(
        order_id
    )

    order.status = "Cancelled"

    db.session.commit()

    log_activity(
        current_user().username,
        f"Cancel Order #{order.id}"
    )

    return redirect(
        url_for(
            "operator.dashboard"
        )
    )


##################################################
# ASSIGN DRIVER
##################################################

@operator_bp.route(
    "/orders/<int:order_id>/assign",
    methods=["POST"]
)
@role_required("operator", "admin")
def assign_driver(order_id):

    order = Order.query.get_or_404(
        order_id
    )

    driver = User.query.get_or_404(
        request.form["driver_id"]
    )

    if (
        not driver.active
        or driver.role != "driver"
    ):

        flash(
            "لا يمكن تعيين سائق معطّل"
        )

        return redirect(
            url_for(
                "operator.orders"
            )
        )

    order.driver_id = driver.id

    order.status = "Assigned"

    sync_order_driver_commission(
        order,
        driver=driver
    )

    db.session.commit()

    log_activity(
        current_user().username,
        f"Assign Driver {driver.username} To Order #{order.id}"
    )

    return redirect(
        url_for(
            "operator.dashboard"
        )
    )


##################################################
# REASSIGN
##################################################

@operator_bp.route(
    "/orders/<int:order_id>/reassign",
    methods=["POST"]
)
@role_required("operator", "admin")
def reassign_driver(order_id):

    order = Order.query.get_or_404(
        order_id
    )

    driver = User.query.get_or_404(
        request.form["driver_id"]
    )

    if (
        not driver.active
        or driver.role != "driver"
    ):

        flash(
            "لا يمكن تعيين سائق معطّل"
        )

        return redirect(
            url_for(
                "operator.orders"
            )
        )

    order.driver_id = driver.id

    order.status = "Assigned"

    order.decline_reason = None

    sync_order_driver_commission(
        order,
        driver=driver
    )

    db.session.commit()

    log_activity(
        current_user().username,
        f"Reassign Order #{order.id}"
    )

    return redirect(
        url_for(
            "operator.dashboard"
        )
    )


##################################################
# SEARCH ORDERS
##################################################

@operator_bp.route("/orders")
@role_required("operator", "admin")
def orders():

    search = request.args.get(
        "search",
        ""
    )

    query = Order.query

    if search:

        query = query.filter(
            db.or_(
                Order.customer_name.contains(
                    search
                ),
                Order.customer_phone.contains(
                    search
                ),
                Order.status.contains(
                    search
                )
            )
        )

    orders = query.order_by(
        Order.id.desc()
    ).all()

    drivers = User.query.filter_by(
        role="driver",
        active=True
    ).all()

    all_routes = RouteCommission.query.all()

    route_commissions = {
        f"{route.from_place_id}-{route.to_place_id}": route.commission
        for route in all_routes
    }

    return render_template(
        "operator/orders.html",
        orders=orders,
        drivers=drivers,
        user=current_user(),
        search=search,
        shops=Shop.query.order_by(
            Shop.name
        ).all(),
        places=Place.query.order_by(
            Place.name
        ).all(),
        route_commissions=route_commissions,
        commission=Setting.query.first()
    )


##################################################
# DRIVER MANAGEMENT
##################################################

@operator_bp.route("/drivers")
@role_required("operator", "admin")
def drivers():

    drivers = User.query.filter_by(
        role="driver"
    ).order_by(
        User.id.desc()
    ).all()

    return render_template(
        "operator/drivers.html",
        drivers=drivers,
        user=current_user()
    )


##################################################
# CREATE DRIVER
##################################################

@operator_bp.route(
    "/drivers/create",
    methods=["POST"]
)
@role_required("operator", "admin")
def create_driver():

    username = (
        request.form["username"]
        .strip()
    )

    exists = User.query.filter_by(
        username=username
    ).first()

    if exists:

        flash(
            "اسم المستخدم موجود مسبقاً"
        )

        return redirect(
            url_for(
                "operator.drivers"
            )
        )

    driver = User(

        username=username,

        full_name=request.form[
            "full_name"
        ],

        password_hash=generate_password_hash(
            request.form[
                "password"
            ]
        ),

        role="driver",

        active=True,

        balance=0,

        status="Available",

        driver_commission_ratio=0.75
    )

    db.session.add(driver)
    db.session.commit()

    log_activity(
        current_user().username,
        f"Create Driver {driver.username}"
    )

    return redirect(
        url_for(
            "operator.drivers"
        )
    )


##################################################
# EDIT DRIVER
##################################################

@operator_bp.route(
    "/drivers/<int:driver_id>/edit",
    methods=["POST"]
)
@role_required("operator", "admin")
def edit_driver(driver_id):

    driver = User.query.get_or_404(
        driver_id
    )

    driver.full_name = (
        request.form[
            "full_name"
        ]
    )

    driver.status = (
        request.form[
            "status"
        ]
    )

    db.session.commit()

    log_activity(
        current_user().username,
        f"Edit Driver {driver.username}"
    )

    return redirect(
        url_for(
            "operator.drivers"
        )
    )


##################################################
# ACTIVATE DRIVER
##################################################

@operator_bp.route(
    "/drivers/<int:driver_id>/toggle"
)
@role_required("operator", "admin")
def toggle_driver(driver_id):

    driver = User.query.get_or_404(
        driver_id
    )

    driver.active = (
        not driver.active
    )

    if driver.active:
        driver.status = "Available"
    else:
        driver.status = "Offline"

    db.session.commit()

    log_activity(
        current_user().username,
        f"Toggle Driver {driver.username}"
    )

    flash(
        "تم تفعيل حساب السائق"
        if driver.active
        else "تم تعطيل حساب السائق — سجل الطلبات والأرصدة محفوظ"
    )

    return redirect(
        url_for(
            "operator.drivers"
        )
    )


##################################################
# SHOPS
##################################################

@operator_bp.route("/shops")
@role_required("operator", "admin")
def shops():

    shops = Shop.query.order_by(
        Shop.name.asc()
    ).all()

    return render_template(
        "operator/shops.html",
        user=current_user(),
        shops=shops,
        places=Place.query.order_by(
            Place.name
        ).all()
    )


##################################################
# CREATE SHOP
##################################################

@operator_bp.route(
    "/shops/create",
    methods=["POST"]
)
@role_required("operator", "admin")
def create_shop():
    existing_shop = Shop.query.filter_by(
        name=request.form["name"].strip()
    ).first()

    if existing_shop:
        flash(
            "المحل موجود مسبقاً"
        )

        return redirect(
            url_for(
                "operator.shops"
            )
        )

    phone, phone_error = validate_phone(
        request.form.get(
            "phone"
        )
    )

    if phone_error:

        flash(phone_error)

        return redirect(
            url_for(
                "operator.shops"
            )
        )

    shop = Shop(

        name=request.form[
            "name"
        ],

        phone=phone,

        place_id=int(
            request.form[
                "place_id"
            ]
        ),

        location_details=request.form.get(
            "location_details",
            ""
        ),

        notes=request.form.get(
            "notes",
            ""
        )

    )

    db.session.add(shop)
    db.session.commit()

    log_activity(
        current_user().username,
        f"Create Shop {shop.name}"
    )

    return redirect(
        url_for(
            "operator.shops"
        )
    )


##################################################
# EDIT SHOP
##################################################

@operator_bp.route(
    "/shops/<int:shop_id>/edit",
    methods=["POST"]
)
@role_required("operator")
def edit_shop(shop_id):

    shop = Shop.query.get_or_404(
        shop_id
    )

    shop.name = request.form[
        "name"
    ]

    phone, phone_error = validate_phone(
        request.form.get(
            "phone"
        )
    )

    if phone_error:

        flash(phone_error)

        return redirect(
            url_for(
                "operator.shops"
            )
        )

    shop.phone = phone

    shop.place_id = int(
        request.form[
            "place_id"
        ]
    )

    shop.location_details = request.form.get(
        "location_details",
        ""
    )

    shop.notes = request.form.get(
        "notes",
        ""
    )

    db.session.commit()

    log_activity(
        current_user().username,
        f"Edit Shop {shop.name}"
    )

    return redirect(
        url_for(
            "operator.shops"
        )
    )


@operator_bp.route("/places")
@role_required("operator")
def places():

    places = (
        Place.query
        .order_by(
            Place.name
        )
        .all()
    )

    all_routes = RouteCommission.query.all()

    seen = set()

    routes = []

    for route in all_routes:

        pair = tuple(
            sorted([
                route.from_place_id,
                route.to_place_id
            ])
        )

        if pair in seen:
            continue

        seen.add(pair)

        routes.append(route)

    return render_template(
        "operator/places.html",
        user=current_user(),
        places=places,
        routes=routes
    )

@operator_bp.route(
    "/places/create",
    methods=["POST"]
)
@role_required("operator")
def create_place():

    from_place_name = (
        request.form.get(
            "from_place",
            ""
        ).strip()
    )

    to_place_name = (
        request.form.get(
            "to_place",
            ""
        ).strip()
    )

    commission = float(
        request.form.get(
            "commission",
            0
        )
    )

    if not from_place_name or not to_place_name:

        return redirect(
            url_for(
                "operator.places"
            )
        )

    from_place = Place.query.filter_by(
        name=from_place_name
    ).first()

    if not from_place:

        from_place = Place(
            name=from_place_name
        )

        db.session.add(
            from_place
        )

        db.session.flush()

    to_place = Place.query.filter_by(
        name=to_place_name
    ).first()

    if not to_place:

        to_place = Place(
            name=to_place_name
        )

        db.session.add(
            to_place
        )

        db.session.flush()

    route1 = RouteCommission.query.filter_by(
        from_place_id=from_place.id,
        to_place_id=to_place.id
    ).first()

    if not route1:

        db.session.add(
            RouteCommission(
                from_place_id=from_place.id,
                to_place_id=to_place.id,
                commission=commission
            )
        )

    route2 = RouteCommission.query.filter_by(
        from_place_id=to_place.id,
        to_place_id=from_place.id
    ).first()

    if not route2:

        db.session.add(
            RouteCommission(
                from_place_id=to_place.id,
                to_place_id=from_place.id,
                commission=commission
            )
        )

    db.session.commit()

    return redirect(
        url_for(
            "operator.places"
        )
    )

@operator_bp.route(
    "/places/delete-route/<int:route_id>"
)
@role_required("operator")
def delete_route(route_id):

    route = RouteCommission.query.get_or_404(
        route_id
    )

    reverse_route = (
        RouteCommission.query
        .filter_by(
            from_place_id=route.to_place_id,
            to_place_id=route.from_place_id
        )
        .first()
    )

    db.session.delete(route)

    if reverse_route:
        db.session.delete(reverse_route)
    from_place_id = route.from_place_id
    to_place_id = route.to_place_id

    db.session.commit()

    for place_id in [from_place_id, to_place_id]:

        remaining_routes = (
            RouteCommission.query.filter(
                (RouteCommission.from_place_id == place_id) |
                (RouteCommission.to_place_id == place_id)
            ).count()
        )

        if remaining_routes == 0:

            place = Place.query.get(place_id)

            if place:
                db.session.delete(place)

    db.session.commit()

    return redirect(
        url_for(
            "operator.places"
        )
    )

@operator_bp.route(
    "/shops/<int:shop_id>/delete"
)
@role_required("operator")
def delete_shop(shop_id):

    shop = Shop.query.get_or_404(
        shop_id
    )

    db.session.delete(shop)

    db.session.commit()

    return redirect(
        url_for(
            "operator.shops"
        )
    )