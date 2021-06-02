# Docker for duplicates removal setup, preparing imagededup installation

FROM tensorflow/tensorflow:2.5.0-gpu

COPY imagededup /opt/imagededup

RUN apt-get update && \
    apt-get install -y python3.8 && \
    apt-get install -y python3.8-dev && \
    echo 'alias python=python3.8' >> ~/.bashrc && \
    python3.8 -m pip install six && \
    python3.8 -m pip install --upgrade pip && \
    python3.8 -m pip install "cython>=0.29" && \
    python3.8 -m pip install --upgrade https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow_gpu-2.5.0-cp38-cp38-manylinux2010_x86_64.whl && \
    cd opt/imagededup && \
    python3.8 setup.py install