import json

from flask import (
    flash,
    redirect,
    url_for
)


OPERATOR_PAGES = {
    "dashboard": {
        "label": "الرئيسية",
        "endpoints": [
            "operator.dashboard",
            "operator.create_order",
        ],
    },
    "orders": {
        "label": "الطلبات",
        "endpoints": [
            "operator.orders",
            "operator.edit_order",
            "operator.cancel_order",
            "operator.assign_driver",
            "operator.reassign_driver",
        ],
    },
    "drivers": {
        "label": "السائقون",
        "endpoints": [
            "operator.drivers",
            "operator.create_driver",
            "operator.edit_driver",
            "operator.toggle_driver",
        ],
    },
    "places": {
        "label": "المناطق",
        "endpoints": [
            "operator.places",
            "operator.create_place",
            "operator.delete_route",
        ],
    },
    "shops": {
        "label": "المحلات",
        "endpoints": [
            "operator.shops",
            "operator.create_shop",
            "operator.edit_shop",
            "operator.delete_shop",
        ],
    },
}

ALL_OPERATOR_PERMISSIONS = list(
    OPERATOR_PAGES.keys()
)

PERMISSION_ORDER = [
    "dashboard",
    "orders",
    "drivers",
    "places",
    "shops",
]

ENDPOINT_PERMISSIONS = {
    endpoint: key
    for key, page in OPERATOR_PAGES.items()
    for endpoint in page["endpoints"]
}


def parse_operator_permissions(
    user
):

    if not user:
        return []

    if not user.operator_permissions:
        return ALL_OPERATOR_PERMISSIONS.copy()

    try:
        stored = json.loads(
            user.operator_permissions
        )
    except (
        TypeError,
        json.JSONDecodeError,
    ):
        return ALL_OPERATOR_PERMISSIONS.copy()

    if not isinstance(
        stored,
        list
    ):
        return ALL_OPERATOR_PERMISSIONS.copy()

    return [
        key
        for key in stored
        if key in OPERATOR_PAGES
    ]


def save_operator_permissions(
    user,
    selected
):

    cleaned = [
        key
        for key in selected
        if key in OPERATOR_PAGES
    ]

    user.operator_permissions = json.dumps(
        cleaned
    )


def operator_has_permission(
    user,
    permission
):

    if not user:
        return False

    if user.role == "admin":
        return True

    if user.role != "operator":
        return False

    return (
        permission
        in parse_operator_permissions(
            user
        )
    )


def endpoint_permission(
    endpoint
):

    return ENDPOINT_PERMISSIONS.get(
        endpoint
    )


def first_allowed_operator_url(
    user
):

    permissions = (
        parse_operator_permissions(
            user
        )
    )

    for key in PERMISSION_ORDER:
        if key in permissions:
            return url_for(
                f"operator.{key}"
            )

    flash(
        "لا توجد صلاحيات مفعّلة لهذا الحساب"
    )

    return url_for(
        "auth.logout"
    )


def enforce_operator_access(
    user,
    endpoint
):

    if (
        not user
        or user.role == "admin"
    ):
        return None

    if user.role != "operator":
        return None

    permission = endpoint_permission(
        endpoint
    )

    if not permission:
        return None

    if operator_has_permission(
        user,
        permission
    ):
        return None

    flash(
        "ليس لديك صلاحية للوصول إلى هذه الصفحة"
    )

    return redirect(
        first_allowed_operator_url(
            user
        )
    )
