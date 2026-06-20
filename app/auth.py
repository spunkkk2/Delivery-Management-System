from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    check_password_hash
)

from .models import User

from .services import (
    log_activity
)

from .permissions import (
    first_allowed_operator_url,
    save_operator_permissions,
    ALL_OPERATOR_PERMISSIONS,
    parse_operator_permissions,
    OPERATOR_PAGES,
)

from .decorators import current_user

auth_bp = Blueprint(
    "auth",
    __name__
)


def redirect_after_login(
    user
):

    if user.role == "admin":

        return redirect(
            url_for(
                "admin.dashboard"
            )
        )

    if user.role == "operator":

        return redirect(
            first_allowed_operator_url(
                user
            )
        )

    return redirect(
        url_for(
            "driver.dashboard"
        )
    )


@auth_bp.route(
    "/",
    methods=["GET", "POST"]
)
def login():

    if request.method == "GET":

        user = current_user()

        if user and user.active:

            return redirect_after_login(
                user
            )

    if request.method == "POST":

        username = (
            request.form["username"]
            .strip()
        )

        password = (
            request.form["password"]
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if not user:

            flash(
                "Invalid username or password"
            )

            return render_template(
                "login.html"
            )

        if not user.active:

            flash(
                "Account disabled"
            )

            return render_template(
                "login.html"
            )

        if not check_password_hash(
            user.password_hash,
            password
        ):

            flash(
                "Invalid username or password"
            )

            return render_template(
                "login.html"
            )

        session.permanent = True

        session["user_id"] = user.id

        log_activity(
            user.username,
            "Login"
        )

        return redirect_after_login(
            user
        )

    return render_template(
        "login.html"
    )


@auth_bp.route("/logout")
def logout():

    if "user_id" in session:

        user = User.query.get(
            session["user_id"]
        )

        if user:

            log_activity(
                user.username,
                "Logout"
            )

    session.clear()

    return redirect(
        url_for(
            "auth.login"
        )
    )