FROM ubuntu:25.04 AS epoch-build

# Install vcpkg to the root directory, as sometimes that makes things easier?
WORKDIR /

# Install the relevant dependencies for vcpkg, and a python enviroment (make sure this matches the later version)
# Then get the other utilities we need for vcpkg and the dependencies, and "install" vcpkg
# setting the relevant environment variables too

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        autoconf \
        automake \
        autoconf-archive \
        ca-certificates \
        cmake \
        curl \
        g++ \
        git \
        make \
        pkg-config \
        python3.13 \
        python3.13-dev \
        tar \
        unzip \
        zip

 RUN git clone https://github.com/microsoft/vcpkg.git
WORKDIR /vcpkg
 RUN git checkout c82f74667287d3dc386bce81e44964370c91a289
 RUN ./bootstrap-vcpkg.sh

ENV VCPKG_ROOT="/vcpkg"
ENV PATH="$VCPKG_ROOT:$PATH"

WORKDIR /code

# this is a horrible bunch of copying, but it avoid cache-busting from changes to epoch_server
COPY epoch_lib Epoch/epoch_lib
COPY epoch_py Epoch/epoch_py
COPY epoch_test Epoch/epoch_test
COPY CMakeLists.txt Epoch
COPY CMakePresets.json Epoch
COPY vcpkg.json Epoch
COPY vcpkg-configuration.json Epoch


WORKDIR /code/Epoch
## Build python bindings and copy the file from its horrible location to somewhere saner
RUN rm -rf ./build \
    && cmake . --preset=python-linux -DCMAKE_CXX_COMPILER=g++ -DCMAKE_MAKE_PROGRAM=make -Wno-dev \
    && cmake --build --preset=python-rel-linux -j \
    && cp /code/Epoch/build/epoch_py/epoch_simulator.cpython-313-x86_64-linux-gnu.so /code/

# Set up the Demo FastAPI server

FROM ubuntu:25.04

WORKDIR /code
RUN apt-get update && apt-get install -y --no-install-recommends python3.13 python3.13-venv
# Add /code/install to both PATH and PYTHONPATH so that we don't have to know the relative path to Epoch
ENV PATH="/code/install:$PATH"
ENV PYTHONPATH="/code/install:${PYTHONPATH}"

COPY epoch_server epoch_server
RUN python3.13 -m venv ./venv/ && ./venv/bin/pip install --no-cache-dir --upgrade -r epoch_server/requirements.txt

COPY --from=epoch-build /code/epoch_simulator.cpython-313-x86_64-linux-gnu.so /code/install/
EXPOSE 8763
CMD ["./venv/bin/python", "-m", "fastapi", "run", "./epoch_server/app/main.py", "--port", "8763"]
