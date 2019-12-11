# Dockex Ubuntu 16.04 Installation:

## Table of Contents

1. [Install Docker-CE v19.03.5](#InstallDockerCE)

2. [Clone Dockex](#CloneDockex)

3. [Optional: NVIDIA GPU Support](#GPUSupport)

4. [Test the Installation](#TestInstallation)

<a name="InstallDockerCE"></a>
## 1. Install Docker-CE v19.03.5

Uninstall previous versions of Docker.

```
sudo apt-get remove docker docker-engine docker.io containerd runc
```

Add the Docker repository.

```
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
```

Install Docker-CE v19.03.5.

```
sudo apt-get update
sudo apt-get install -y docker-ce=5:19.03.5~3-0~ubuntu-xenial docker-ce-cli=5:19.03.5~3-0~ubuntu-xenial containerd.io
```

Start and enable Docker
```
sudo systemctl start docker
sudo systemctl enable docker
```

Verify the version matches 19.03.5 by running the following.

```
docker --version
```

Dockex requires the ability to 
[manage Docker as a non-root user](https://docs.docker.com/install/linux/linux-postinstall/). This has system security 
implications that are discussed [here](https://docs.docker.com/engine/security/security/#docker-daemon-attack-surface). 

To allow managing Docker as a non-root user, run the following.

```
sudo groupadd docker
sudo usermod -aG docker $USER
newgrp docker
```

Then restart the system.

```
sudo reboot
```

<a name="CloneDockex"></a>
## 2. Clone Dockex

Change directory to the desired Dockex install location and clone the repository.

```
git clone https://github.com/ConnexonSystems/dockex.git
```

<a name="GPUSupport"></a>
## 3. Optional: NVIDIA GPU Support

Dockex supports the use of NVIDIA GPUs through [nvidia-docker](https://github.com/NVIDIA/nvidia-docker). 

To make GPU hardware available to Dockex modules, first install the NVIDIA drivers for your GPU(s). One way to achieve 
this is to install CUDA with the following. 

```
curl -O http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/cuda-repo-ubuntu1604_10.0.130-1_amd64.deb
sudo dpkg -i cuda-repo-ubuntu1604_10.0.130-1_amd64.deb
sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1604/x86_64/7fa2af80.pub

sudo apt-get update
sudo apt install -y build-essential
sudo apt-get install -y cuda
```

Reboot the system to enable the driver.

```sudo reboot```

Install and activate nvidia-docker by running the following.

```
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

If the installation was successful, running ```nvidia-smi``` in an ubuntu Docker container should show GPU utilization 
statistics.

```
docker run -it --rm --gpus all ubuntu
nvidia-smi
```

Press ctrl-d to exit the container.

If the nvidia-docker installation was successfull, enable GPU utilization by Dockex. Create a ```user_config.json``` 
file by copying ```dockex/base_config.json```. Then edit ```user_config.json``` to set ```enable_gpus``` to ```true```.

```
cd /path/to/dockex
cp base_config.json user_config.json
nano user_config.json  # set "enable_gpus" to true and save
```

<a name="TestInstallation"></a>
## 4. Test the Installation

Start Dockex by launching the Dockex bootstrap script.

```
bash /path/to/dockex/dockex_bootstrap/dockex_bootstrap.sh
```

Dockex will then build and run its microservices. You can monitor its progress by watching currently running Docker 
containers with the following. Hit ctrl-C to exit.

```
watch -n 1 docker container ls
```

Once all Dockex microservices have started, open a browser and navigate to ```127.0.0.1:3001``` to access the Dockex 
GUI.
