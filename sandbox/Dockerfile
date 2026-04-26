FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    g++ cmake \
    default-jdk \
    wget \
    libgtest-dev \
    && pip3 install pytest \
    && apt-get clean

# build Google Test for C++
RUN cd /usr/src/gtest && cmake . && make && cp lib/*.a /usr/lib/

# download JUnit for Java
RUN mkdir -p /usr/local/junit && \
    wget -q https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.10.0/junit-platform-console-standalone-1.10.0.jar \
    -O /usr/local/junit/junit.jar

WORKDIR /code
