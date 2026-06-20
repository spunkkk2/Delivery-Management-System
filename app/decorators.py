from functools import wraps
from flask import session, redirect, url_for

from .models import User


def current_user():

    if "user_id" not in session:
        return None

    return User.query.get(
        session["user_id"]
    )


def login_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated


def role_required(*roles):

    def wrapper(f):

        @wraps(f)
        def decorated(*args, **kwargs):

            if "user_id" not in session:
                return redirect(
                    url_for("auth.login")
                )

            user = User.query.get(
                session["user_id"]
            )

            if not user:
                session.clear()

                return redirect(
                    url_for("auth.login")
                )

            if user.role not in roles:
                return redirect(
                    url_for("auth.login")
                )

            return f(*args, **kwargs)

        return decorated

    return wrapper