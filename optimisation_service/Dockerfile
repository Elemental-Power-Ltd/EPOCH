FROM python:3.13-slim-trixie AS epoch-build

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
        libtool \
        make \
        pkg-config \
        python3.13 \
        python3.13-dev \
        tar \
        unzip \
        zip
        
RUN git clone https://github.com/microsoft/vcpkg.git
WORKDIR /vcpkg

RUN ./bootstrap-vcpkg.sh

ENV VCPKG_ROOT="/vcpkg"
ENV PATH="$VCPKG_ROOT:$PATH"

WORKDIR /code
COPY ./epoch_simulator epoch
WORKDIR /code/epoch
# Build python bindings and copy the file from its horrible location to somewhere saner
RUN rm -rf ./build \
    && cmake . --preset=python-linux -DCMAKE_CXX_COMPILER=g++ -DCMAKE_MAKE_PROGRAM=make -Wno-dev \
    && cmake --build --preset=python-rel-linux -j

# Put the FastAPI and python sections in their own container
FROM astral/uv:python3.13-trixie-slim
ENV UV_COMPILE_BYTECODE=1

WORKDIR /code

# Copy requirements
COPY uv.lock pyproject.toml ./

RUN uv sync --frozen --no-dev

# Add /code/install to both PATH and PYTHONPATH so that we don't have to know the relative path to Epoch
ENV PATH="/code/install:$PATH"
ENV PYTHONPATH="/code/install:${PYTHONPATH}"

# Copy the python bindings and executable
COPY ./optimisation_service/app app
COPY --from=epoch-build /code/epoch/build/epoch_py/epoch_simulator.cpython-313-x86_64-linux-gnu.so /code/install/

ENV UV_NO_SYNC=1
EXPOSE 8761
CMD ["uv", "run", "fastapi", "run", "./app/main.py", "--port", "8761"]
