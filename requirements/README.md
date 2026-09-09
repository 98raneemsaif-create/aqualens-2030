# Frozen runtime installation

`runtime.in` records direct project pins. `runtime.lock` is the complete 195-package Linux/Python 3.11 inventory from the approved preflight. `airflow-3.3.1-python3.11.constraints.txt` is the unmodified official Airflow constraints snapshot from:

https://raw.githubusercontent.com/apache/airflow/constraints-3.3.1/constraints-3.11.txt

Its SHA-256 is `9fe2d4a54b8ac8450f63ffce0b195de8d9027ddc21bc40653b62be91a63fa366`.

The Dockerfile extends the pinned official Airflow image and creates an isolated Python 3.11 virtual environment. It installs `torch==2.14.0+cpu` **with `--no-deps` from `https://download.pytorch.org/whl/cpu` only**, then installs the full lock from PyPI with the official Airflow constraints. The second installation sees the exact CPU torch version already satisfied and installs its pinned dependencies. This prevents a future build from selecting CUDA-enabled torch and its large NVIDIA dependency set. Do not replace the CPU pin with an unqualified torch release, use an unconstrained install, or enable `--system-site-packages`.

The upstream image's optional packages are outside the active virtual environment. Only the resolved runtime and its transitive dependencies are installed into it. Transitive packages such as telemetry, FastAPI, and Kubernetes client libraries are not extra runtime services. No Spark, Celery, Redis, ZooKeeper, Marquez, or Chroma server service is installed/configured by this scaffold. Model weights are not image build inputs.

For a future explicitly authorized lock refresh, use the same official constraints and CPU routing:

```text
uv pip compile requirements/runtime.in --constraint requirements/airflow-3.3.1-python3.11.constraints.txt --python-version 3.11 --python-platform x86_64-unknown-linux-gnu --torch-backend cpu --output-file requirements/runtime.lock --no-header --no-annotate
```

Do not refresh pins during routine builds. The Dockerfile applies constraints and runs `pip check`; the runtime smoke check verifies every locked package version and `torch.version.cuda is None`. Import checks do not establish scored pipeline implementation.
