# choice of python version
ARG VARIANT=3.12-slim-bookworm
FROM python:${VARIANT}

# install hatch
RUN apt update && apt install -y wget xz-utils
RUN wget https://github.com/pypa/hatch/releases/latest/download/hatch-x86_64-unknown-linux-gnu.tar.gz -O - \
    | tar -xz -C /usr/local/bin && hatch --version

# install helix
RUN wget https://github.com/helix-editor/helix/releases/download/24.03/helix-24.03-x86_64-linux.tar.xz -O - \
    | tar -xJ -C /usr/local && mv /usr/local/helix* /usr/local/helix
ENV PATH="${PATH}:/usr/local/helix"
