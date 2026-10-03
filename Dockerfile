FROM python:3.14-alpine
WORKDIR /usr/src/harness
# Optionally pin the installed version so `build-all` can rebuild historical versions.
# An empty value (the normal build) installs the latest release.
ARG IMPLEMENTATION_VERSION
RUN python3 -m pip install --no-cache-dir "corvus-json-schema-rs${IMPLEMENTATION_VERSION:+==${IMPLEMENTATION_VERSION}}"
COPY bowtie_corvus.py .
CMD ["python3", "bowtie_corvus.py"]
