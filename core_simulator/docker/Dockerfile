FROM ubuntu:22.04

# install systyem pre-reqs

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:ubuntu-toolchain-r/test && \
    apt-get update && \
    apt-get install -y \
    gcc-13 \
    g++-13 \
    cmake \
    ninja-build \
    autoconf \
    automake \
    autoconf-archive \
    libtool \
    m4 \
    make \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-13 100 && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-13 100


WORKDIR /EP

# Set up vcpkg

RUN apt-get update && \
    apt-get install -y git curl zip unzip tar pkg-config
RUN git clone https://github.com/microsoft/vcpkg.git
RUN ./vcpkg/bootstrap-vcpkg.sh

ENV VCPKG_ROOT=/EP/vcpkg

# Build Epoch

RUN apt-get update && \ 
    apt-get install -y libmimalloc-dev

ENV MIMALLOC_SO=/usr/lib/x86_64-linux-gnu/libmimalloc.so

COPY . ./Epoch

WORKDIR /EP/Epoch
RUN cmake -DCMAKE_CXX_COMPILER=g++-13 --preset headless-linux
RUN cmake --build --preset=headless-rel-linux

CMD ["sh", "-c", "LD_PRELOAD=${MIMALLOC_SO} ./build/epoch_main/Epoch"]
