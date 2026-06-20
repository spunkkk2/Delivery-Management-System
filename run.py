from flask_migrate import upgrade

from app import create_app, seed_defaults

app = create_app()

with app.app_context():
    upgrade()
    seed_defaults()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5006,
        debug=True
    )