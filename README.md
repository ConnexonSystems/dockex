[![DOI](https://zenodo.org/badge/219467652.svg)](https://zenodo.org/badge/latestdoi/219467652)

![Alt text](docs/img/dockex_black.svg)

Dockex is an open-source orchestration and monitoring tool for easily running local or distributed computational experiments 
using containers. NVIDIA GPU support is included.

## Under Development:

This is a pre-release version of Dockex that is under active development. Please consider this version experimental. 
Tests and documentation are coming soon at which point we will welcome contributors!

## Table of Contents

1. [Introduction](#Introduction)

2. [Installation](#Installation)

3. [Getting Started](#GettingStarted)

4. [Documentation](#Documentation)

5. [Citing Dockex](#CitingDockex)  

<a name="Introduction"></a>
## Introduction

As a machine learning and data science infrastructure, Dockex enables the development of easily shareable code 
"modules" that run in self-contained containers. With Dockex, there is no more finding exciting code only to 
waste hours figuring out the required installation process and picking through the source to discover how you can 
integrate it into your workflow. When using a new Dockex module, no additional installation is required, and software 
interfaces are defined in readable JSON files.

Experiment configuration files coded in Python (which also run inside containers) capture how modules are 
instantiated into "jobs". Experiments define the parameters, inputs, and outputs of jobs.

Users launch experiments using the Dockex GUI which is a React application that runs locally on your machine. Dockex 
automatically manages the execution of experiments by extracting parallelism and running experiment jobs only once 
their input dependencies are met. Resource utilization is controlled through a CPU/GPU credits system that defines how 
many jobs can run at one time.  

If multiple Dockex machines are present on a network, Dockex automatically 
forms a cluster computer for distributed experiment execution. Your code is automatically deployed to the other 
machines and built without any intervention.

<a name="Installation"></a>
## Installation

Dockex officially supports Ubuntu 16.04 and Ubuntu 18.04. Expanded operating system support is coming soon.

Installation consists of installing Docker-CE v19.03.5 and cloning the Dockex repository. 

For GPU support, you must have NVIDIA drivers installed and enable a flag in the Dockex configuration file.

For Ubuntu 16.04 installation instructions, see [here](docs/ubuntu_1604_install.md).

For Ubuntu 18.04 installation instructions, see [here](docs/ubuntu_1804_install.md).

<a name="GettingStarted"></a>
## Getting Started

Once Dockex is installed, start the system by calling the bootstrap script.

```bash /path/to/dockex/dockex_bootstrap/dockex_bootstrap.sh```

When launched for the first time, Dockex will build the required images and launch its microservices. You can 
monitor the startup process by watching the list of active containers.

```watch -n 1 docker container ls```

Once the following 16 containers are listed as running, startup is complete.

```
app_server
cluster_monitor
credits_monitor
credits_updater
decrement_dependency
dockex_machine_identifier
dockex_machine_monitor
dockex_redis
dockex_webdis
experiment_worker
hardware_monitor
json_launcher
machine_discovery
output_saver
progress_monitor
redis_launcher
```

You can then access the Dockex GUI by opening a browser and navigating to ```127.0.0.1:3001```.

### Example Experiment
You can find a self-contained mnist_experiment example [here](https://github.com/ChrisHeelan/mnist_experiment).

To run the experiment:

1. Clone the repository.

    ```
    git clone https://github.com/ChrisHeelan/mnist_experiment
    ```

2. Navigate to the Dockex ```LAUNCH``` screen, and submit the following.

    * Project Path: ```/path/to/mnist_experiment```
    * Experiment Path: ```experiments/mnist_experiment.py```

    Dockex will build the modules to prepare the experiment. Note that building modules initially may take some 
    time; however, the process is typically much shorter when running modules subsequent times (assuming you don't 
    remove the images).

3. Navigate to the ```MACHINES``` screen and increase the number of available CPU credits (e.g. 4) to control the 
number of parallel jobs. In mnist_experiment, each job requires 1 CPU credit to run.

4. Monitor the experiment execution on the ```PROGRESS``` screen. Results will be written to the tmp_dockex_path 
(defaults to ```/tmp/dockex/data```).

<a name="Documentation"></a>
## Documentation

Coming soon!

<a name="CitingDockex"></a>
## Citing Dockex

If you use Dockex in a scientific publication, we would appreciate citations to this repository: 

```
@software{dockex,
  author       = {ChrisHeelan},
  title        = {ConnexonSystems/dockex: Initial Release},
  month        = dec,
  year         = 2019,
  publisher    = {Zenodo},
  version      = {v0.0.1},
  doi          = {10.5281/zenodo.3570735},
  url          = {https://doi.org/10.5281/zenodo.3570735}
}
```
