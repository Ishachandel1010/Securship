<<<<<<< HEAD
# SecureShip — a Jenkins CI/CD pipeline with a DevSecOps twist

A tiny Flask URL-shortener API, wrapped in a Jenkins pipeline that
does more than "build and deploy." Most beginner Jenkins tutorials
stop at that. This one adds the two stages that actually make a
pipeline "DevSecOps": static code security scanning (Bandit) and
container image vulnerability scanning (Trivy) — plus a simplified
blue-green deploy so a bad build never touches your live traffic.

## Why this project (and not another "hello world" pipeline)

You already know GitHub Actions, SAST/DAST, and blue-green deploys
from your AWS/Zetheta work. The *new* thing here is Jenkins itself —
its UI, its credential store, its agent model, and the Groovy-based
Jenkinsfile syntax. So the project deliberately reuses concepts you
already understand (security gates, blue-green) and puts them in a
tool you're learning for the first time. That's a much faster way to
get comfortable with Jenkins than starting from a "print hello"
pipeline and building up.

## Architecture

```
 GitHub push
      |
      v
 +-----------+     +-------+     +------------+     +-------------+
 | Checkout  | --> | Lint  | --> | Unit Tests | --> | SAST (Bandit)|
 +-----------+     +-------+     +------------+     +-------------+
                                                            |
                                                            v
 +----------------+     +--------------------+     +---------------+
 | Push to        | <-- | Trivy image scan   | <-- | Build Docker   |
 | Docker Hub     |     | (blocks on HIGH/   |     | image          |
 +----------------+     |  CRITICAL CVEs)    |     +---------------+
      |                 +--------------------+
      v
 +------------------+     +-------------+     +------------------+
 | Deploy "green"   | --> | Smoke test  | --> | Promote to "live"|
 | container :5001  |     | /health     |     | container :5000  |
 +------------------+     +-------------+     +------------------+
```

If any stage fails, the pipeline stops there — the currently live
container is never touched, so a broken build can't take down what's
already running.

## What's in this repo

| File | Purpose |
|---|---|
| `app/app.py` | The Flask app (URL shortener) |
| `app/requirements.txt` | Runtime dependencies only |
| `requirements-dev.txt` | Adds pytest, flake8, bandit for CI |
| `tests/test_app.py` | Unit tests the pipeline runs |
| `Dockerfile` | Multi-stage build, non-root user, gunicorn |
| `Jenkinsfile` | The full pipeline definition |

## Prerequisites

- Docker Desktop (or Docker Engine) installed
- A free Docker Hub account (for the image push stage)
- A GitHub repo to hold this code (Jenkins polls/webhooks this)

## Step-by-step setup

### 1. Push this code to GitHub
Create a new repo and push these files as-is — the Jenkinsfile lives
at the repo root, which is where Jenkins expects to find it.

### 2. Run Jenkins itself (in Docker, so nothing touches your host)
```bash
docker run -d --name jenkins \
  -p 8080:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(which docker):/usr/bin/docker \
  jenkins/jenkins:lts
```
Mounting `docker.sock` lets Jenkins run `docker build`/`docker run`
commands on your host's Docker engine — this is the standard way to
give a containerized Jenkins access to Docker itself.

Open `http://localhost:8080`, unlock it with the initial admin
password (`docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword`),
and install the suggested plugins.

### 3. Install Trivy on the Jenkins container
```bash
docker exec -u root jenkins bash -c \
  "apt-get update && apt-get install -y wget && \
   wget https://github.com/aquasecurity/trivy/releases/download/v0.54.1/trivy_0.54.1_Linux-64bit.deb && \
   dpkg -i trivy_0.54.1_Linux-64bit.deb"
```

### 4. Add your Docker Hub credentials to Jenkins
Manage Jenkins → Credentials → System → Global credentials → Add
Credentials → kind "Username with password" → ID: `dockerhub-creds`.
This ID must match the `credentials('dockerhub-creds')` line in the
Jenkinsfile — Jenkins injects it as `$DOCKERHUB_USR` / `$DOCKERHUB_PSW`
automatically, which is why the password never appears in plain text
anywhere in the pipeline.

### 5. Create the pipeline job
New Item → Pipeline → under "Pipeline" section choose "Pipeline
script from SCM" → SCM: Git → paste your repo URL → Script Path:
`Jenkinsfile`.

### 6. Run it
Click "Build Now" and watch the stage view populate. Try:
```bash
curl -X POST http://localhost:5000/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://anthropic.com"}'
```

### 7. Break it on purpose (this is the actual learning step)
- Change a test in `tests/test_app.py` to expect the wrong status
  code → push → watch the pipeline stop at "Unit Tests" and the
  live container stay untouched.
- Add `import subprocess; subprocess.call(user_input, shell=True)`
  somewhere in `app.py` (don't deploy this!) → push → watch Bandit
  flag it in the SAST stage.

Seeing the pipeline *catch* a problem is worth more than seeing it
pass.

## Extension ideas, roughly in order of effort
1. Add a Slack/webhook notification in the `post` block on success/failure.
2. Swap the in-memory dict for Redis (`docker run redis` + a second
   deploy stage) — now you're doing multi-container orchestration.
3. Replace the port-swap "blue-green" with an actual Nginx reverse
   proxy container that flips its upstream config.
4. Add a DAST stage using OWASP ZAP's baseline scan against the
   deployed "green" container before promoting it — this is the
   natural next step given the DAST work you already did on the
   Zetheta project, just running inside Jenkins instead of GitHub
   Actions.
5. Move credentials/config to a `Jenkinsfile` parameterized build so
   the same pipeline can deploy to "staging" vs "prod" targets.
=======
# Securship
This is for Jenkins with CICD pipeline project
>>>>>>> 9e34216242a6ec943b1e4295dc8e95edd29bb947
