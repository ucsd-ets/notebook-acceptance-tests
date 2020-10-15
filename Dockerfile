FROM elgalu/selenium:3.141

USER root

COPY test-ui.py /opt/datahub/test-ui.py
COPY test-rstudio-ui.py /opt/datahub/test-rstudio-ui.py