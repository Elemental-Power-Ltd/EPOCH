FROM python:3.12.4-alpine3.20 AS epoch-build

# Install vcpkg to the root directory, as sometimes that makes things easier?
WORKDIR /

# Install the relevant dependencies for vcpkg:
# we use pip to install ninja because the version in APK is too old (3.9, vcpkg needs 3.10)
# Then get the other utilities we need for vcpkg and the dependencies, and "install" vcpkg
# setting the relevant environment variables too
RUN pip install ninja
RUN apk update
RUN apk add --no-cache g++ cmake make git curl zip unzip tar pkgconfig
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
RUN cmake . --preset=python-linux -DCMAKE_CXX_COMPILER=g++
RUN cmake --build --preset=python-rel-linux -j

# Copy the file from its horrible location back down to the core location.
RUN cp /code/Epoch/build/epoch_py/epoch_simulator.cpython-312-x86_64-linux-musl.so /code/
RUN rm -rf ./build
# Build headless release
RUN cmake . --preset=headless-linux -DCMAKE_CXX_COMPILER=g++
RUN cmake --build --preset=headless-rel-linux -j
# Strip debug symbols from Epoch before we copy it out of the build image
RUN strip /code/Epoch/build/epoch_main/Epoch


FROM python:3.12.4-alpine3.20

WORKDIR /code
RUN apk add --no-cache libstdc++

# Add /code/install to both PATH and PYTHONPATH so that we don't have to know the relative path to Epoch
ENV PATH="/code/install:$PATH"
ENV PYTHONPATH="/code/install:$PYTHONPATH"

# Copy the python bindings
COPY --from=epoch-build /code/epoch_simulator.cpython-312-x86_64-linux-musl.so /code/install/
# Copy the executable
COPY --from=epoch-build /code/Epoch/build/epoch_main/Epoch /code/install/

# Finally, we can configure our python code!
# Install all the requirements, watching out for those that cause trouble for Alpine.
COPY requirements.txt .
COPY requirements requirements
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY app app

EXPOSE 8761
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8761"]