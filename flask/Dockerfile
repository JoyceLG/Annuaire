FROM python:3.12-slim

# FLASK_APP dans l'image : toute commande `flask` lancée dans le conteneur
# (promouvoir, peupler) trouve l'application, .env n'étant pas copié. Le
# serveur, lui, est Gunicorn, qui reçoit l'application dans son CMD.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=annuaire:creer_app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /bin/bash appuser
USER appuser

COPY . .

EXPOSE 5000
CMD ["gunicorn", "--config", "gunicorn.conf.py", "annuaire:creer_app()"]