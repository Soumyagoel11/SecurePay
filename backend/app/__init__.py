import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, jsonify

from app.extensions import db, jwt, cors
from config import Config, TestingConfig

from app.routes import (
    auth_bp, wallet_bp, payments_bp, fraud_bp,
    refunds_bp, admin_bp, merchant_bp, customer_bp,
    qr_bp,
)


def create_app(config_class=None) -> Flask:
    app = Flask(__name__)
    if config_class is None:
        app.config.from_object(Config)
    else:
        app.config.from_object(config_class)

    # Load .env if present
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    # Re-apply object config after dotenv load (env vars can override)
    if config_class is None:
        app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    _configure_logging(app)
    _register_error_handlers(app)
    _register_blueprints(app)

    # Import models so they are registered with SQLAlchemy before create_all
    from app import models  # noqa: F401

    with app.app_context():
        db.create_all()

    return app


def _configure_logging(app: Flask):
    if not app.debug and not app.testing:
        if not os.path.exists("logs"):
            os.makedirs("logs")
        file_handler = RotatingFileHandler(
            "logs/securepay.log", maxBytes=102400, backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s [%(module)s] %(message)s"
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("SecurePay backend starting up")


def _register_blueprints(app: Flask):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
    app.register_blueprint(payments_bp, url_prefix="/api/payments")
    app.register_blueprint(fraud_bp, url_prefix="/api/fraud")
    app.register_blueprint(refunds_bp, url_prefix="/api/refunds")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(merchant_bp, url_prefix="/api/merchant")
    app.register_blueprint(customer_bp, url_prefix="/api/customer")
    app.register_blueprint(qr_bp, url_prefix="/api/qr-payments")


def _register_error_handlers(app: Flask):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(success=False, message="Bad request"), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify(success=False, message="Unauthorized"), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify(success=False, message="Forbidden"), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(success=False, message="Resource not found"), 404

    @app.errorhandler(409)
    def conflict(e):
        return jsonify(success=False, message="Conflict"), 409

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify(success=False, message="Unprocessable entity"), 422

    @app.errorhandler(500)
    def server_error(e):
        app.logger.exception("Internal server error")
        return jsonify(success=False, message="Internal server error"), 500

    # JWT-specific error handlers (registered on the jwt extension).
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify(success=False, message="Token expired"), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify(success=False, message="Invalid token"), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify(success=False, message="Missing or invalid token"), 401


def create_app_for_testing() -> Flask:
    return create_app(TestingConfig)
