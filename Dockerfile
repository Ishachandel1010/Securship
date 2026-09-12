# --- Stage 1: build a clean set of dependencies ---
# Using a slim base image keeps the final image small, which also
# means fewer packages for the container scanner to flag.
FROM python:3.12-slim AS builder

WORKDIR /build
COPY app/requirements.txt .
COPY app/ ./app/
COPY tests/ ./tests/
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: minimal runtime image ---
# We copy only the installed packages and app code from the builder
# stage, so build tools (gcc, pip cache, etc.) never end up in the
# image that actually ships. Smaller image = smaller attack surface.
FROM python:3.12-slim

# The base image is built periodically upstream, so by the time you
# pull it, Debian's security team may have already shipped patches
# for some of its packages (e.g. gzip, sqlite3, perl). This picks
# those up at build time instead of shipping known-fixed CVEs.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Run as a non-root user — a classic, easy container-security win
# that most beginner Dockerfiles skip. Trivy (our scanner) will flag
# "running as root" if we don't do this.
RUN useradd --create-home --uid 1000 appuser
WORKDIR /home/appuser/app

COPY --from=builder /root/.local /home/appuser/.local
COPY app/ ./app/

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=5000

USER appuser
EXPOSE 5000

# gunicorn is a production-grade WSGI server — using Flask's dev
# server (app.run) in a real deployment is itself a common security
# finding, so we avoid it here.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app.app:app"]

