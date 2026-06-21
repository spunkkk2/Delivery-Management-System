from datetime import (
    datetime,
    date,
    timedelta
)

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

from sqlalchemy import func

from . import db

from .decorators import (
    role_required,
    current_user
)

from .models import (
    User,
    Order,
    Shop,
    Setting,
    ActivityLog,
    DriverLedger,
    CompanyExpense,
    Place,
    RouteCommission
)

from .services import (
    log_activity,
    calculate_company_share
)

from .permissions import (
    save_operator_permissions,
    ALL_OPERATOR_PERMISSIONS,
    parse_operator_permissions,
    OPERATOR_PAGES,
)

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


EXPENSE_CATEGORIES = [
    "عام",
    "رواتب",
    "إيجار",
    "وقود",
    "صيانة",
    "تسويق",
    "أخرى",
]


def _parse_date(
    value,
    default=None
):

    if not value:
        return default

    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d"
        ).date()
    except ValueError:
        return default


def _order_company_share(
    order
):

    return calculate_company_share(
        order.commission,
        order.driver_commission
    )


def _filter_source():

    if (
        request.args.get("date_from")
        or request.args.get("date_to")
    ):
        return request.args

    if (
        request.form.get("date_from")
        or request.form.get("date_to")
    ):
        return request.form

    return request.args


def _accounting_filters():

    source = _filter_source()

    today = date.today()
    default_from = (
        today - timedelta(days=30)
    )

    date_from = _parse_date(
        source.get("date_from"),
        default_from
    )

    date_to = _parse_date(
        source.get("date_to"),
        today
    )

    payment_type = (
        source.get(
            "payment_type",
            ""
        ).strip()
    )

    driver_id = (
        source.get(
            "driver_id",
            ""
        ).strip()
    )

    shop_id = (
        source.get(
            "shop_id",
            ""
        ).strip()
    )

    category = (
        source.get("filter_category")
        or source.get("category", "")
    ).strip()

    sort = (
        source.get(
            "sort",
            "date_desc"
        ).strip()
    )

    return {
        "date_from": date_from,
        "date_to": date_to,
        "payment_type": payment_type,
        "driver_id": driver_id,
        "shop_id": shop_id,
        "category": category,
        "sort": sort,
    }


def _filter_orders(
    filters
):

    start = datetime.combine(
        filters["date_from"],
        datetime.min.time()
    )

    end = datetime.combine(
        filters["date_to"]
        + timedelta(days=1),
        datetime.min.time()
    )

    query = Order.query.filter(
        Order.status == "Delivered",
        Order.created_at >= start,
        Order.created_at < end,
    )

    if filters["payment_type"]:
        query = query.filter(
            Order.payment_type
            == filters["payment_type"]
        )

    if filters["driver_id"]:
        query = query.filter(
            Order.driver_id
            == int(
                filters["driver_id"]
            )
        )

    if filters["shop_id"]:
        query = query.filter(
            Order.shop_id
            == int(
                filters["shop_id"]
            )
        )

    return query.all()


def _filter_expenses(
    filters
):

    query = CompanyExpense.query.filter(
        CompanyExpense.expense_date
        >= filters["date_from"],
        CompanyExpense.expense_date
        <= filters["date_to"],
    )

    if filters["category"]:
        query = query.filter(
            CompanyExpense.category
            == filters["category"]
        )

    return query.all()


def _sort_orders(
    orders,
    sort_key
):

    if sort_key == "date_asc":
        orders.sort(
            key=lambda o: o.created_at
        )

    elif sort_key == "revenue_desc":
        orders.sort(
            key=_order_company_share,
            reverse=True
        )

    elif sort_key == "revenue_asc":
        orders.sort(
            key=_order_company_share
        )

    elif sort_key == "commission_desc":
        orders.sort(
            key=lambda o: o.commission
            or 0,
            reverse=True
        )

    else:
        orders.sort(
            key=lambda o: o.created_at,
            reverse=True
        )

    return orders


def _accounting_redirect(
    filters
):

    return redirect(
        url_for(
            "admin.accounting",
            date_from=filters[
                "date_from"
            ].isoformat(),
            date_to=filters[
                "date_to"
            ].isoformat(),
            payment_type=filters[
                "payment_type"
            ],
            driver_id=filters[
                "driver_id"
            ],
            shop_id=filters[
                "shop_id"
            ],
            category=filters[
                "category"
            ],
            sort=filters["sort"],
        )
    )


@admin_bp.route("/")
@role_required("admin")
def dashboard():

    total_orders = Order.query.count()

    active_orders = Order.query.filter(
        Order.status.in_(
            [
                "Pending",
                "Assigned",
                "Accepted",
                "Picked Up"
            ]
        )
    ).count()

    completed_orders = Order.query.filter_by(
        status="Delivered"
    ).count()

    declined_orders = Order.query.filter_by(
        status="Declined"
    ).count()

    cancelled_orders = Order.query.filter_by(
        status="Cancelled"
    ).count()

    drivers_count = User.query.filter_by(
        role="driver"
    ).count()

    operators_count = User.query.filter_by(
        role="operator"
    ).count()

    shops_count = Shop.query.count()

    company_owes_drivers = (
        db.session.query(
            func.sum(User.balance)
        ).filter(
            User.role == "driver",
            User.balance > 0
        ).scalar() or 0
    )

    drivers_owe_company = (
        db.session.query(
            func.sum(
                func.abs(User.balance)
            )
        ).filter(
            User.role == "driver",
            User.balance < 0
        ).scalar() or 0
    )

    orders = Order.query.order_by(
        Order.id.desc()
    ).limit(20).all()

    logs = ActivityLog.query.order_by(
        ActivityLog.id.desc()
    ).limit(50).all()

    drivers = User.query.filter_by(
        role="driver"
    ).all()

    operators = User.query.filter_by(
        role="operator"
    ).all()

    shops = Shop.query.order_by(
        Shop.name.asc()
    ).all()

    setting = Setting.query.first()

    return render_template(
        "admin/dashboard.html",
        user=current_user(),
        total_orders=total_orders,
        active_orders=active_orders,
        completed_orders=completed_orders,
        declined_orders=declined_orders,
        cancelled_orders=cancelled_orders,
        drivers_count=drivers_count,
        operators_count=operators_count,
        shops_count=shops_count,
        company_owes_drivers=company_owes_drivers,
        drivers_owe_company=drivers_owe_company,
        orders=orders,
        logs=logs,
        drivers=drivers,
        operators=operators,
        shops=shops,
        setting=setting
    )


####################################################
# USERS
####################################################

@admin_bp.route("/users")
@role_required("admin")
def users():

    users = User.query.order_by(
        User.id.desc()
    ).all()

    permissions_map = {
        u.id: parse_operator_permissions(u)
        for u in users
    }

    return render_template(
        "admin/users.html",
        users=users,
        user=current_user(),
        permissions_map=permissions_map,
        operator_pages=OPERATOR_PAGES,
        all_operator_permissions=(
            ALL_OPERATOR_PERMISSIONS
        ),
    )


@admin_bp.route(
    "/users/create",
    methods=["POST"]
)
@role_required("admin")
def create_user():

    username = request.form["username"].strip()

    full_name = request.form["full_name"].strip()

    password = request.form["password"]

    role = request.form["role"]

    existing = User.query.filter_by(
        username=username
    ).first()

    if existing:

        flash("اسم المستخدم موجود مسبقاً")

        return redirect(
            url_for("admin.users")
        )

    user = User(
        username=username,
        full_name=full_name,
        role=role,
        password_hash=generate_password_hash(
            password
        )
    )

    if role == "operator":
        save_operator_permissions(
            user,
            request.form.getlist(
                "permissions"
            )
            or ALL_OPERATOR_PERMISSIONS
        )

    db.session.add(user)
    db.session.commit()

    log_activity(
        current_user().username,
        f"Created User: {username}"
    )

    return redirect(
        url_for("admin.users")
    )


@admin_bp.route(
    "/users/<int:user_id>/edit",
    methods=["POST"]
)
@role_required("admin")
def edit_user(user_id):

    user = User.query.get_or_404(
        user_id
    )

    user.full_name = request.form[
        "full_name"
    ]

    user.role = request.form[
        "role"
    ]

    if user.role == "driver":
        user.status = request.form.get(
            "status",
            "Available"
        )
        user.operator_permissions = None

    elif user.role == "operator":
        save_operator_permissions(
            user,
            request.form.getlist(
                "permissions"
            )
        )

    else:
        user.operator_permissions = None

    db.session.commit()

    log_activity(
        current_user().username,
        f"Edited User: {user.username}"
    )

    return redirect(
        url_for("admin.users")
    )


@admin_bp.route(
    "/users/<int:user_id>/toggle"
)
@role_required("admin")
def toggle_user(user_id):

    user = User.query.get_or_404(
        user_id
    )

    user.active = not user.active

    db.session.commit()

    log_activity(
        current_user().username,
        f"Toggle User: {user.username}"
    )

    return redirect(
        url_for("admin.users")
    )


####################################################
# COMMISSION SETTINGS
####################################################

@admin_bp.route(
    "/commission",
    methods=["POST"]
)
@role_required("admin")
def update_commission():

    setting = Setting.query.first()

    setting.default_commission = float(
        request.form["commission"]
    )

    db.session.commit()

    log_activity(
        current_user().username,
        "Updated Commission"
    )

    return redirect(
        url_for("admin.dashboard")
    )


####################################################
# BALANCES
####################################################

@admin_bp.route("/balances")
@role_required("admin")
def balances():

    drivers = User.query.filter_by(
        role="driver"
    ).order_by(
        User.full_name.asc()
    ).all()

    return render_template(
        "admin/balances.html",
        drivers=drivers,
        user=current_user()
    )


@admin_bp.route(
    "/balances/<int:user_id>",
    methods=["POST"]
)
@role_required("admin")
def update_balance(user_id):

    driver = User.query.get_or_404(
        user_id
    )

    driver.balance = float(
        request.form["balance"]
    )

    db.session.commit()

    log_activity(
        current_user().username,
        f"Updated Balance: {driver.username}"
    )

    return redirect(
        url_for("admin.balances")
    )


####################################################
# DRIVER LEDGER
####################################################

@admin_bp.route(
    "/ledger/<int:driver_id>"
)
@role_required("admin")
def ledger(driver_id):

    driver = User.query.get_or_404(
        driver_id
    )

    entries = DriverLedger.query.filter_by(
        driver_id=driver.id
    ).order_by(
        DriverLedger.id.desc()
    ).all()

    return render_template(
        "admin/ledger.html",
        driver=driver,
        entries=entries,
        user=current_user()
    )


####################################################
# SHOPS
####################################################

@admin_bp.route("/shops")
@role_required("admin")
def shops():

    shops = Shop.query.order_by(
        Shop.name.asc()
    ).all()

    return render_template(
        "admin/shops.html",
        shops=shops,
        user=current_user()
    )


@admin_bp.route(
    "/shops/<int:shop_id>/edit",
    methods=["POST"]
)
@role_required("admin")
def edit_shop(shop_id):

    shop = Shop.query.get_or_404(
        shop_id
    )

    shop.name = request.form["name"]

    shop.phone = request.form["phone"]

    shop.notes = request.form["notes"]

    try:
        discount_ratio = float(
            request.form.get(
                "discount_ratio",
                0
            ) or 0
        )
    except ValueError:
        discount_ratio = 0

    shop.discount_ratio = max(
        0,
        min(
            100,
            discount_ratio
        )
    )

    db.session.commit()

    log_activity(
        current_user().username,
        f"Edited Shop: {shop.name}"
    )

    return redirect(
        url_for("admin.shops")
    )


@admin_bp.route(
    "/shops/<int:shop_id>/delete"
)
@role_required("admin")
def delete_shop(shop_id):

    shop = Shop.query.get_or_404(
        shop_id
    )

    name = shop.name

    db.session.delete(shop)
    db.session.commit()

    log_activity(
        current_user().username,
        f"Deleted Shop: {name}"
    )

    return redirect(
        url_for("admin.shops.html")
    )


####################################################
# PLACES
####################################################

@admin_bp.route("/places")
@role_required("admin")
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
        "admin/places.html",
        user=current_user(),
        places=places,
        routes=routes
    )


@admin_bp.route(
    "/places/create",
    methods=["POST"]
)
@role_required("admin")
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
                "admin.places"
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

    log_activity(
        current_user().username,
        f"Created route: {from_place_name} - {to_place_name}"
    )

    return redirect(
        url_for(
            "admin.places"
        )
    )


@admin_bp.route(
    "/places/delete-route/<int:route_id>"
)
@role_required("admin")
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

    log_activity(
        current_user().username,
        f"Deleted route #{route_id}"
    )

    return redirect(
        url_for(
            "admin.places"
        )
    )


####################################################
# ORDERS
####################################################

@admin_bp.route("/orders")
@role_required("admin")
def orders():

    orders = Order.query.order_by(
        Order.id.desc()
    ).all()

    drivers = User.query.filter_by(
        role="driver",
        active=True
    ).all()

    return render_template(
        "admin/orders.html",
        orders=orders,
        drivers=drivers,
        user=current_user()
    )


####################################################
# SEARCH
####################################################

@admin_bp.route("/search")
@role_required("admin")
def search():

    query = request.args.get(
        "q",
        ""
    ).strip()

    orders = Order.query.filter(
        db.or_(
            Order.customer_name.contains(
                query
            ),
            Order.customer_phone.contains(
                query
            ),
            Order.status.contains(
                query
            )
        )
    ).all()

    drivers = User.query.filter(
        User.full_name.contains(
            query
        )
    ).all()

    shops = Shop.query.filter(
        Shop.name.contains(
            query
        )
    ).all()

    return render_template(
        "admin/search.html",
        query=query,
        orders=orders,
        drivers=drivers,
        shops=shops,
        user=current_user()
    )


####################################################
# DRIVERS
####################################################

@admin_bp.route("/drivers")
@role_required("admin")
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


@admin_bp.route(
    "/drivers/create",
    methods=["POST"]
)
@role_required("admin")
def create_driver():

    username = request.form["username"].strip()

    exists = User.query.filter_by(
        username=username
    ).first()

    if exists:

        flash("اسم المستخدم موجود مسبقاً")

        return redirect(
            url_for("admin.drivers")
        )

    driver = User(
        username=username,
        full_name=request.form["full_name"],
        password_hash=generate_password_hash(
            request.form["password"]
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
        url_for("admin.drivers")
    )


@admin_bp.route(
    "/drivers/<int:driver_id>/edit",
    methods=["POST"]
)
@role_required("admin")
def edit_driver(driver_id):

    driver = User.query.get_or_404(
        driver_id
    )

    driver.full_name = request.form["full_name"]
    driver.status = request.form["status"]

    ratio_percent = float(
        request.form[
            "driver_commission_ratio"
        ]
    )

    driver.driver_commission_ratio = round(
        max(0, min(100, ratio_percent)) / 100,
        4
    )

    db.session.commit()

    log_activity(
        current_user().username,
        f"Edit Driver {driver.username}"
    )

    return redirect(
        url_for("admin.drivers")
    )


@admin_bp.route(
    "/drivers/<int:driver_id>/toggle"
)
@role_required("admin")
def toggle_driver(driver_id):

    driver = User.query.get_or_404(
        driver_id
    )

    driver.active = not driver.active

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
        url_for("admin.drivers")
    )


####################################################
# ACCOUNTING
####################################################

@admin_bp.route("/accounting")
@role_required("admin")
def accounting():

    filters = _accounting_filters()

    orders = _filter_orders(
        filters
    )

    orders = _sort_orders(
        orders,
        filters["sort"]
    )

    expenses = _filter_expenses(
        filters
    )

    expenses.sort(
        key=lambda e: (
            e.expense_date,
            e.id
        ),
        reverse=True
    )

    total_commission = sum(
        float(o.commission or 0)
        for o in orders
    )

    total_driver_commission = sum(
        float(
            o.driver_commission or 0
        )
        for o in orders
    )

    total_revenue = sum(
        _order_company_share(o)
        for o in orders
    )

    cash_orders = [
        o for o in orders
        if o.payment_type == "Cash"
    ]

    paid_orders = [
        o for o in orders
        if o.payment_type == "Paid"
    ]

    cash_revenue = sum(
        _order_company_share(o)
        for o in cash_orders
    )

    paid_revenue = sum(
        _order_company_share(o)
        for o in paid_orders
    )

    total_expenses = sum(
        float(e.amount)
        for e in expenses
    )

    net_profit = (
        total_revenue
        - total_expenses
    )

    expense_by_category = {}

    for expense in expenses:
        key = (
            expense.category
            or "أخرى"
        )

        expense_by_category[key] = (
            expense_by_category.get(
                key,
                0
            )
            + float(expense.amount)
        )

    daily_revenue = {}

    for order in orders:
        day_key = (
            order.created_at.strftime(
                "%Y-%m-%d"
            )
        )

        daily_revenue[day_key] = (
            daily_revenue.get(
                day_key,
                0
            )
            + _order_company_share(
                order
            )
        )

    chart_labels = sorted(
        daily_revenue.keys()
    )

    chart_values = [
        round(
            daily_revenue[label],
            2
        )
        for label in chart_labels
    ]

    company_owes_drivers = (
        db.session.query(
            func.sum(User.balance)
        ).filter(
            User.role == "driver",
            User.balance > 0
        ).scalar() or 0
    )

    drivers_owe_company = (
        db.session.query(
            func.sum(
                func.abs(User.balance)
            )
        ).filter(
            User.role == "driver",
            User.balance < 0
        ).scalar() or 0
    )

    all_drivers = User.query.filter_by(
        role="driver"
    ).order_by(
        User.full_name.asc()
    ).all()

    all_shops = Shop.query.order_by(
        Shop.name.asc()
    ).all()

    avg_order_revenue = (
        round(
            total_revenue
            / len(orders),
            2
        )
        if orders
        else 0
    )

    margin_percent = (
        round(
            (
                total_revenue
                / total_commission
            )
            * 100,
            1
        )
        if total_commission
        else 0
    )

    return render_template(
        "admin/accounting.html",
        user=current_user(),
        filters=filters,
        orders=orders,
        expenses=expenses,
        total_commission=total_commission,
        total_driver_commission=(
            total_driver_commission
        ),
        total_revenue=total_revenue,
        cash_revenue=cash_revenue,
        paid_revenue=paid_revenue,
        cash_count=len(cash_orders),
        paid_count=len(paid_orders),
        delivered_count=len(orders),
        total_expenses=total_expenses,
        net_profit=net_profit,
        expense_by_category=(
            expense_by_category
        ),
        chart_labels=chart_labels,
        chart_values=chart_values,
        company_owes_drivers=(
            company_owes_drivers
        ),
        drivers_owe_company=(
            drivers_owe_company
        ),
        all_drivers=all_drivers,
        all_shops=all_shops,
        avg_order_revenue=(
            avg_order_revenue
        ),
        margin_percent=margin_percent,
        expense_categories=(
            EXPENSE_CATEGORIES
        ),
    )


@admin_bp.route(
    "/accounting/expenses",
    methods=["POST"]
)
@role_required("admin")
def add_expense():

    filters = _accounting_filters()

    expense_date = _parse_date(
        request.form.get(
            "expense_date"
        ),
        date.today()
    )

    amount = float(
        request.form["amount"]
    )

    if amount <= 0:

        flash(
            "يجب أن يكون المبلغ أكبر من صفر"
        )

        return _accounting_redirect(
            filters
        )

    expense = CompanyExpense(
        description=request.form[
            "description"
        ].strip(),
        amount=amount,
        category=request.form.get(
            "category",
            "أخرى"
        ),
        expense_date=expense_date,
        notes=request.form.get(
            "notes",
            ""
        ).strip(),
        created_by=current_user().username,
    )

    db.session.add(expense)
    db.session.commit()

    log_activity(
        current_user().username,
        f"Add Expense: {expense.description}"
    )

    flash("تمت إضافة المصروف")

    return _accounting_redirect(
        filters
    )


@admin_bp.route(
    "/accounting/expenses/<int:expense_id>/delete",
    methods=["POST"]
)
@role_required("admin")
def delete_expense(expense_id):

    filters = _accounting_filters()

    expense = CompanyExpense.query.get_or_404(
        expense_id
    )

    description = expense.description

    db.session.delete(expense)
    db.session.commit()

    log_activity(
        current_user().username,
        f"Delete Expense: {description}"
    )

    flash("تم حذف المصروف")

    return _accounting_redirect(
        filters
    )


####################################################
# LOGS
####################################################

@admin_bp.route("/logs")
@role_required("admin")
def logs():

    logs = ActivityLog.query.order_by(
        ActivityLog.id.desc()
    ).all()

    return render_template(
        "admin/logs.html",
        logs=logs,
        user=current_user()
    )