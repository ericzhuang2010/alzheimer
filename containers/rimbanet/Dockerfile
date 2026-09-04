FROM rocker/r-ver:4.3.3

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash bc bcftools build-essential ca-certificates git gsl-bin libgsl-dev \
    perl plink2 python3 python3-pip python3-venv time zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN Rscript -e 'install.packages(c("BiocManager","data.table","digest","jsonlite","MatrixEQTL","yaml","cit"), repos="https://cloud.r-project.org"); BiocManager::install("edgeR", version="3.18", ask=FALSE, update=FALSE)'
RUN python3 -m venv /opt/rimbanet-venv \
    && /opt/rimbanet-venv/bin/pip install --no-cache-dir \
    "h5py>=3.11,<4" "networkx>=3.3,<4" "numpy>=1.26,<3" "pandas>=2.1,<3" \
    "PyYAML>=6,<7" "scipy>=1.11,<2"

# This source tree is intentionally gitignored. Build only after cloning the
# pinned commit documented in config/seaad_rimbanet.yml.
COPY external_tools/BayesianNetwork /opt/rimbanet-src

RUN mkdir -p /opt/xerces-src /opt/xerces \
    && tar -xzf /opt/rimbanet-src/src/xerces-c-src_2_8_0.tar.gz \
       -C /opt/xerces-src --strip-components=1 \
    && cd /opt/xerces-src/src/xercesc \
    && export XERCESCROOT=/opt/xerces-src \
    && ./runConfigure -p linux -c gcc -x g++ -r pthread -P /opt/xerces \
    && make \
    && make install

RUN set -eux; \
    cd /opt/rimbanet-src/src; \
    sed -i 's|^XMLROOT = .*|XMLROOT = /opt/xerces|' Makefile; \
    sed -i 's| -O -DLINUX -c| -O -std=gnu++98 -DLINUX -c|' Makefile; \
    make clean || true; \
    make -j"$(nproc)"; \
    install -m 0755 testBN /usr/local/bin/testBN; \
    install -m 0755 /opt/rimbanet-src/script/generateBIF /usr/local/bin/generateBIF

ENV LD_LIBRARY_PATH=/opt/xerces/lib
ENV RIMBANET_ROOT=/opt/rimbanet-src
ENV PATH=/opt/rimbanet-venv/bin:${PATH}
WORKDIR /work
