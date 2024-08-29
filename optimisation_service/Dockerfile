FROM python:3.12.4-alpine3.20

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
RUN ./bootstrap-vcpkg.sh
ENV VCPKG_ROOT="/vcpkg"
ENV PATH="$VCPKG_ROOT:$PATH"


WORKDIR /code
COPY . .

# Build EPOCH using CMake.
# This process is currently a bit hacky: first configure it with the python present and some preloaded settings,
# then actually build it.
# Finally, copy the file from its horrible location back down to the core location.
WORKDIR /code/Epoch
RUN rm -rf ./build
RUN cmake . --preset=python -B build -DCMAKE_CXX_COMPILER=g++ -DCMAKE_MAKE_PROGRAM=make -DCMAKE_POSITION_INDEPENDENT_CODE=ON
RUN cmake --build --preset=python-rel -j
RUN cp /code/Epoch/build/epoch_py/epoch_simulator.cpython-312-x86_64-linux-musl.so /code/

# Finally, we can configure our python code!
# Install all the requirements, watching out for those that cause trouble for Alpine.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
WORKDIR /code


EXPOSE 8761
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8761"]