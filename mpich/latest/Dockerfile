FROM alfianisnan26/konfersi-mpi/konfersi-mpi:base

WORKDIR ${WORKDIR}
USER ${USER}

ENV NETCDF=/usr \
    NETCDF_classic=1

RUN sudo apt update && sudo apt install csh \
    gfortran \
    m4 \
    mpich \
    libhdf5-mpich-dev \
    libpng-dev \
    libnetcdff-dev \
    netcdf-bin \
    ncl-ncarg \
    build-essential -y

WORKDIR ${USER_HOME}/wrf_installer

# download install jasper
RUN wget https://www.ece.uvic.ca/~frodo/jasper/software/jasper-1.900.29.tar.gz
RUN tar xvf jasper-1.900.29.tar.gz 
RUN jasper-1.900.29/configure --prefix=/opt/jasper-1.900.29
RUN make
RUN sudo make install

# download install wrf
RUN wget https://github.com/wrf-model/WRF/archive/v4.2.1.tar.gz
RUN tar xvf v4.2.1.tar.gz

RUN wget https://github.com/wrf-model/WPS/archive/v4.2.tar.gz
RUN tar xvf v4.2.tar.gz

# configure wrf
WORKDIR ${USER_HOME}/wrf_installer/WRF-4.2.1
RUN echo "34" | ./configure
RUN sed -i '/-lwrfio_nf -L\/usr\/lib/ {s/[[:space:]]*$//; s/$/ -lnetcdff -lnetcdf/}' ./configure.wrf
# compile wrf
RUN ./compile -j 2 em_real 2>&1 | tee compile.log

# configure wps
WORKDIR ${USER_HOME}/wrf_installer/WPS-4.2
ENV WRF_DIR=${USER_HOME}/wrf_installer/WRF-4.2.1/
ENV JASPERLIB=/opt/jasper-1.900.29/lib/
ENV JASPERINC=/opt/jasper-1.900.29/include/
RUN echo "1" | ./configure
RUN sed -i '/-L$(NETCDF)\/lib  -lnetcdf/ s/$/ -lnetcdff/' ./configure.wps
# compile wps
RUN ./compile 2>&1 | tee compile.log

# Move WRF and WPS to ${USER_HOME}/wrf and ${USER_HOME}/wps
RUN mv ${USER_HOME}/wrf_installer/WRF-4.2.1 ${USER_HOME}/wrf
RUN mv ${USER_HOME}/wrf_installer/WPS-4.2 ${USER_HOME}/wps

WORKDIR ${USER_HOME}/workspace

CMD ["mpi_bootstrap"]