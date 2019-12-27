ARG PYTHON_VERSION="3.6"
FROM python:${PYTHON_VERSION}-stretch AS builder

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG NODE_VERSION="8.x"
# hadolint ignore=DL3008
RUN curl -sL "https://deb.nodesource.com/setup_${NODE_VERSION}" | bash - \
 && apt-get install --no-install-recommends -y \
      nodejs

ARG HADOLINT_VERSION=v1.17.1
RUN curl -fsSL "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-$(uname -m)" -o /usr/local/bin/hadolint  \
  && chmod +x /usr/local/bin/hadolint

COPY tools/install-mssql.sh /prophet/tools/install-mssql.sh
RUN /prophet/tools/install-mssql.sh --dev

COPY app/server/static/package*.json /prophet/app/server/static/
WORKDIR /prophet/app/server/static
RUN npm ci

COPY requirements.txt /
RUN pip install -r /requirements.txt \
 && pip wheel -r /requirements.txt -w /deps

COPY Dockerfile /
RUN hadolint /Dockerfile

COPY . /prophet

WORKDIR /prophet
RUN tools/ci.sh

FROM builder AS cleaner

WORKDIR /prophet/app/server/static
RUN SOURCE_MAP=False DEBUG=False npm run build \
 && rm -rf components pages node_modules .*rc package*.json webpack.config.js

WORKDIR /prophet
RUN python app/manage.py collectstatic --noinput

FROM python:${PYTHON_VERSION}-slim-stretch AS runtime

COPY --from=builder /prophet/tools/install-mssql.sh /prophet/tools/install-mssql.sh
RUN /prophet/tools/install-mssql.sh

RUN useradd -ms /bin/sh prophet

RUN mkdir /data \
 && chown prophet:prophet /data

COPY --from=builder /deps /deps
# hadolint ignore=DL3013
RUN pip install --no-cache-dir /deps/*.whl

COPY --from=cleaner --chown=prophet:prophet /prophet /prophet

VOLUME /data
ENV DATABASE_URL="sqlite:////data/prophet.db"

ENV DEBUG="True"
ENV SECRET_KEY="change-me-in-production"
ENV PORT="8000"
ENV WORKERS="2"
ENV GOOGLE_TRACKING_ID=""
ENV AZURE_APPINSIGHTS_IKEY=""

USER prophet
WORKDIR /prophet
EXPOSE ${PORT}

CMD ["/prophet/tools/run.sh"]
