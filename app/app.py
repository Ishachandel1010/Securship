"""
SecureShip - a tiny URL shortener API.

This is intentionally simple: an in-memory dict as the "database".
The point of this project isn't the app itself — it's the pipeline
that tests, scans, builds, and deploys it. Keeping the app small means
you spend your learning time on Jenkins concepts, not Flask concepts.
"""

import hashlib
import os
from flask import Flask, request, jsonify, redirect, render_template

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

# In-memory store: { short_code: original_url }
# NOTE: this resets every time the container restarts. That's fine for
# a learning project — swapping this for Redis/Postgres is a great
# "next step" extension once the pipeline itself is working.
URL_STORE = {}


def make_short_code(url: str) -> str:
    """Generate a short, deterministic code for a given URL.

    Using the first 6 hex chars of a sha256 hash keeps this simple and
    avoids needing any external ID-generation library.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return digest[:6]


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint.

    Jenkins (and any real deployment) needs a fast, dependency-free way
    to confirm the container is actually serving traffic after deploy.
    This is what the pipeline's "smoke test" stage will hit.
    """
    return jsonify(status="ok"), 200


@app.route("/shorten", methods=["POST"])
def shorten():
    """Accepts {"url": "https://..."} and returns a short code."""
    data = request.get_json(silent=True) or {}
    url = data.get("url")

    if not url or not url.startswith(("http://", "https://")):
        # Basic input validation — deliberately strict so the unit
        # tests have something meaningful to check.
        return jsonify(error="Provide a valid absolute URL"), 400

    code = make_short_code(url)
    URL_STORE[code] = url
    return jsonify(short_code=code, original_url=url), 201


@app.route("/<code>", methods=["GET"])
def resolve(code):
    """Redirects a short code back to its original URL."""
    url = URL_STORE.get(code)
    if not url:
        return jsonify(error="Short code not found"), 404
    return redirect(url, code=302)


if __name__ == "__main__":
    # host=0.0.0.0 is required so the app is reachable from outside
    # the Docker container, not just from inside it.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
