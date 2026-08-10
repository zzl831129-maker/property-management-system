FROM python:3.10-slim

RUN useradd -m -u 1000 user

USER user

ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

COPY --chown=user requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user . .

EXPOSE 10000

ENTRYPOINT ["sh", "-c", "mkdir -p $HOME/.streamlit && printf '%s' \"$STREAMLIT_SECRETS\" > $HOME/.streamlit/secrets.toml && streamlit run app.py --server.port=${PORT:-10000} --server.address=0.0.0.0"]
