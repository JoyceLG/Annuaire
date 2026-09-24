FROM python:3.12-slim

# FLASK_APP dans l'image : toute commande `flask` lancée dans le conteneur
# (run, promouvoir, peupler) trouve l'application, .env n'étant pas copié.
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
CMD ["flask", "run", "--host", "0.0.0.0"]