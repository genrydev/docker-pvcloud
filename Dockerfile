FROM python:3.6-alpine

#ARGUMENTOS
#ARG GITLAB_USER
#ARG GITLAB_PASSWORD

# Install new packages
RUN apk add --update build-base python3-dev py-pip jpeg-dev zlib-dev libffi-dev openssl-dev git openssh-client sshpass libxml2-dev libxslt-dev

# Upgrade pip
RUN pip install --upgrade pip

# Change LIBRARY_PATH environment variable because of error in building zlib
ENV LIBRARY_PATH=/lib:/usr/lib
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

# Install ansible
ARG ANSIBLE_VERSION=2.5

RUN pip install ansible==$ANSIBLE_VERSION

# Install pyvcloud module
RUN pip install pyvcloud

# Create new group and user
#RUN addgroup ansiblegrp && adduser -D -G ansiblegrp ansibleusr
RUN addgroup ansiblegrp -g 10101 && adduser -D -G ansiblegrp -u 10101  ansibleusr

# Permissions assignments
RUN mkdir -p /var/ansible && chown -R ansibleusr:ansiblegrp /var/ansible
RUN mkdir /var/ansible/pyvcloud && chown -R ansibleusr:ansiblegrp /var/ansible/pyvcloud && chmod -R u=rwX,g=rwX,o=rX /var/ansible/pyvcloud
COPY pyvcloud/ /var/ansible/pyvcloud/

# Define volumes
#VOLUME [ "/var/ansible" ]

# Set Workdir
WORKDIR /var/ansible

#RUN cd  /var/ansible && git clone http://${GITLAB_USER}:${GITLAB_PASSWORD}@gitlab.accsa.uy/agesic/pyvcloud.git
# Copy initial script
COPY run.sh /var/ansible
COPY uid_entrypoint /var/ansible
# Copy test playbook
COPY main-test.yml /var/ansible/pyvcloud

RUN chmod -R u+x,g+x /var/ansible/uid_entrypoint /var/ansible/run.sh && chgrp -R 0 /var/ansible && chmod -R g=u /var/ansible /etc/passwd

# Set non-root User
USER 10101

# Set entrypoint
ENTRYPOINT [ "/var/ansible/uid_entrypoint" ]
# Set command
CMD ["./run.sh"]
