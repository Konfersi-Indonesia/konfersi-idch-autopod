FROM ubuntu:20.04

LABEL maintainer="alfian@isnan.me"

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Update and install base dependencies
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y sudo build-essential \
    ca-certificates \
    wget \
    openssl \
    perl \
    mpich \
    python3 \
    linux-headers-$(uname -r) \
    nano \
    bash \
    curl \
    python3-pip \
    openssh-server \
    bind9-host \
    nano \
    dnsutils \
    net-tools \
    iputils-ping \
    && apt-get clean

#### CLEAN UP ####
WORKDIR /

#### ADD DEFAULT USER ####
ARG USER=mpi
ENV USER=${USER}
RUN useradd -m ${USER} \
    && echo "${USER}   ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ENV USER_HOME=/home/${USER}
RUN chown -R ${USER}:${USER} ${USER_HOME}

#### CREATE WORKING DIRECTORY FOR USER ####
ARG WORKDIR=/workspace
ENV WORKDIR=${WORKDIR}
RUN mkdir -p ${WORKDIR} \
    && chown -R ${USER}:${USER} ${WORKDIR}

RUN mkdir -p /etc/ssh
RUN /usr/bin/ssh-keygen -A

RUN sed -i "s/#PasswordAuthentication.*/PasswordAuthentication no/" /etc/ssh/sshd_config \
    && sed -i "s/#PermitRootLogin.*/PermitRootLogin no/" /etc/ssh/sshd_config \
    && sed -i "s/#AuthorizedKeysFile/AuthorizedKeysFile/" /etc/ssh/sshd_config \
    && sed -i "s/#HostKey/HostKey/" /etc/ssh/sshd_config

RUN mkdir -p /run/sshd
RUN chown root:root /run/sshd
RUN chmod 0755 /run/sshd

ENV SSHDIR=${USER_HOME}/.ssh
RUN mkdir -p ${SSHDIR} \
    && chown -R ${USER}:${USER} ${SSHDIR}

COPY ssh/ ${SSHDIR}/
RUN cat ${SSHDIR}/*.pub >> ${SSHDIR}/authorized_keys

RUN echo "StrictHostKeyChecking no" > ${SSHDIR}/config \
    && chmod 600 ${SSHDIR}/* \
    && chown ${USER}:${USER} ${SSHDIR}/*

RUN curl -fsSL https://code-server.dev/install.sh | sh

COPY mpi_bootstrap /usr/local/bin/mpi_bootstrap
RUN chmod +x /usr/local/bin/mpi_bootstrap

COPY get_hosts /usr/local/bin/get_hosts
RUN chmod +x /usr/local/bin/get_hosts

COPY auto_update_hosts /usr/local/bin/auto_update_hosts
RUN chmod +x /usr/local/bin/auto_update_hosts

ENV HYDRA_HOST_FILE=/etc/opt/hosts
RUN touch ${HYDRA_HOST_FILE} && chown ${USER}:${USER} ${HYDRA_HOST_FILE}

WORKDIR ${WORKDIR}
USER ${USER}

CMD ["/bin/bash"]