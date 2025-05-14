FROM ubuntu:24.10 AS epoch-build

# Install vcpkg to the root directory, as sometimes that makes things easier?
WORKDIR /

# Install the relevant dependencies for vcpkg:
# we use pip to install ninja because the version in APK is too old (3.9, vcpkg needs 3.10)
# Then get the other utilities we need for vcpkg and the dependencies, and "install" vcpkg
# setting the relevant environment variables too

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        cmake \
        curl \
        g++ \
        git \
        make \
        pkg-config \
        python3 \
        python3-dev \
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
COPY Epoch Epoch

# Build EPOCH using CMake.
# This process is currently a bit hacky: first configure it with the python present and some preloaded settings,
# then actually build it.
WORKDIR /code/Epoch
# Build python bindings 
RUN rm -rf ./build
RUN cmake . --preset=python-linux -DCMAKE_CXX_COMPILER=g++ -DCMAKE_MAKE_PROGRAM=make -Wno-dev \
    && cmake --build --preset=python-rel-linux -j \
    && cp /code/Epoch/build/epoch_py/epoch_simulator.cpython-312-x86_64-linux-gnu.so /code/

# Build headless release
RUN rm -rf ./build \
    && cmake . --preset=headless-linux -DCMAKE_CXX_COMPILER=g++ -DCMAKE_MAKE_PROGRAM=make -Wno-dev \
    && cmake --build --preset=headless-rel-linux -j \
    && strip /code/Epoch/build/epoch_main/Epoch
# Strip debug symbols from Epoch before we copy it out of the build image


FROM ubuntu:24.10

WORKDIR /code
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip python3-venv
# Add /code/install to both PATH and PYTHONPATH so that we don't have to know the relative path to Epoch
ENV PATH="/code/install:$PATH"
ENV PYTHONPATH="/code/install:$PYTHONPATH"

# RUN pip install llvmlite
# Copy the python bindings
COPY --from=epoch-build /code/epoch_simulator.cpython-312-x86_64-linux-gnu.so /code/install/
# Copy the executable
COPY --from=epoch-build /code/Epoch/build/epoch_main/Epoch /code/install/

# Finally, we can configure our python code!
# Install all the requirements, watching out for those that cause trouble for Alpine.
COPY requirements.txt .
COPY requirements requirements

# We're using Ubuntu instead of the python image, so put the
# files for our app in a venv to avoid mangling the default ones
RUN python3 -m venv ./venv/.
RUN ./venv/bin/pip install --no-cache-dir --upgrade -r requirements.txt

COPY app app

EXPOSE 8761
CMD ["./venv/bin/python", "-m", "fastapi", "run", "./app/main.py", "--port", "8761"]