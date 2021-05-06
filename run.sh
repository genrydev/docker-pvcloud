#!/bin/sh

echo PWD=$(pwd)
echo ID=$(id -u)

if [ -z "$ANSIBLE_PLAYBOOK" ]
then
   ANSIBLE_PLAYBOOK = "main-ansible-test.yml"
fi
echo ANSIBLE_PLAYBOOK=${ANSIBLE_PLAYBOOK}

if [ -z "$VAPP_NAME" ]
then
  VAPP_NAME = "newvapp"
fi
echo VAPP_NAME=${VAPP_NAME}

if [ -z "$VM_NAME" ]
then
   VM_NAME = "newvm"
fi
echo VM_NAME=${VM_NAME}

cd /var/ansible

if [ -z "$DEBUG" ]
then
    echo Ejecutando el playbook: ${ANSIBLE_PLAYBOOK} ......
    cd pyvcloud && ansible-playbook ${ANSIBLE_PLAYBOOK} -e "vapp_name=${VAPP_NAME}" -e "vm_name=${VM_NAME}" 
fi
