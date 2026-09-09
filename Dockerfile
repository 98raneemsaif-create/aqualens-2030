FROM apache/airflow:3.3.1-python3.11@sha256:efff0a36fb367437fb45ae61f1139fce2a0df255ca9d4ef357e02783e845170f

USER root
RUN mkdir -p /opt/aqualens /opt/airflow/runtime \
    && chown airflow:root /opt/aqualens /opt/airflow/runtime
USER airflow

# Isolate the frozen stack from optional packages bundled in the upstream image.
ENV VIRTUAL_ENV=/opt/aqualens/venv \
    PATH="/opt/aqualens/venv/bin:${PATH}" \
    PYTHONNOUSERSITE=1 \
    PIP_USER=false \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/aqualens/venv
COPY --chown=airflow:root requirements/ /opt/aqualens/requirements/

# Only torch uses the CPU index; no CUDA wheels or model weights are installed.
RUN python -m pip install --no-cache-dir --no-deps \
    --index-url https://download.pytorch.org/whl/cpu 'torch==2.14.0+cpu'
RUN python -m pip install --no-cache-dir \
    --index-url https://pypi.org/simple \
    --constraint /opt/aqualens/requirements/airflow-3.3.1-python3.11.constraints.txt \
    --requirement /opt/aqualens/requirements/runtime.lock \
    && python -m pip check

WORKDIR /opt/airflow
