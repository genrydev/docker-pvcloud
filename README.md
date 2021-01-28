# Pyvcloud Docker Image for OCP

## Descripción

Dockerfile y archivos necesarios para construir la imágen que se va a a utilizar
para ejecutar un playbook ansible con el modulo pyvcloud

La imágen se debe subir a Docker HUB para poder importarla en el OCP

Esta imágen se va a ejecutar utilizando el comando **oc run** dentro de un 
pipeline de Jenkins

Ejemplo de ejecución:

```
oc run pyvcloud  --env ANSIBLE_PLAYBOOK=main.yml \
     --env VM_NAME=vm-ejemplo --attach=True \
     --leave-stdin-open=True --restart=Never \
     --image=docker-registry.default.svc:5000/test-pipelines/pyvcloudv6
```
Variables:

| Variable | Descripción |
| -------- | -------- |
| ANSIBLE_PLAYBOOK   | Determina que playbook va a ejecutar. Si no se pasa va a ejecutar el playbook main-test.yml que está en este proyecto|
| VM_NAME   | Especifica el nombre de la VM a crear, de no especificarla se creara una vm con el nombre **newvm** |

## Construcción de la Imágen

```
git clone http://gitlab.paas.agesic.red.uy/accsa/pyvcloud-docker.git
cd pyvcloud-docker
docker build  -t pyvcloud .
```
