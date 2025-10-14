import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from .db import init_db, get_engine, create_session_factory


def create_app() -> Flask:
	app = Flask(__name__)
	CORS(app)

	# Configuration
	db_url = os.environ.get("DATABASE_URL", f"sqlite:///./data/taxi.db")
	app.config["SQLALCHEMY_DATABASE_URI"] = db_url

	# Ensure data directory exists
	os.makedirs("data", exist_ok=True)

	# Initialize DB and session factory
	engine = get_engine(db_url)
	init_db(engine)
	app.session_factory = create_session_factory(engine)

	# Register API blueprint
	from .api import api_bp
	app.register_blueprint(api_bp, url_prefix="/api")

	# Serve frontend assets for convenience
	@app.get("/")
	def index():
		return send_from_directory("frontend", "index.html")

	@app.get("/assets/<path:path>")
	def assets(path: str):
		return send_from_directory("frontend", path)

	@app.get("/health")
	def health() -> tuple[str, int]:
		return "ok", 200

	return app


