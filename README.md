# EuCanImage Image Preprocessing Toolkit

This repository contains the code for preprocessing images for the EuCanImage project. 

## Building
```
docker build -t eucanimage-image-preprocessing .
```


## Running
```
docker run --rm -v D:\Data03\XNAT:/data -p 9000:9000 eucanimage-image-preprocessing \
    -config_path /data/config/xnat_local.json \
    -data_path /data/local_data \
    -log_level info
```

| Parameter       | Description        |
|-----------------|--------------------|
| --rm  | removes container when run is complete |
| -v D:\Data03\XNAT:/data  | create a temporary volume mount to make local folder accessible to docker |
| -p 9000:9000 | map host port to container port |
| eucanimage-image-preprocessing | the docker image to run |
| -config_path /data/config/xnat_local.json | path to configuration (in relation to docker path) |
| -data_path /data/local_data | path to data store for db and logs (in relation to docker path) |
| -log_level info  | logging level: debug, info, warning, error, critical |

## Configuration

Running the code requires a configuration file. An example configuration file is provided in the /example folder.

The configuration file is a JSON file with the following structure:

```
{
    "xnat_server": "http://host.docker.internal/xnat",
    "xnat_user": "xnat_user",
    "xnat_password": "xnat_password",

    "xnat_projects": ["eucanimage_test"],

    "preprocess_functions": ["quality_functions"],

    "index": true,
    "reset": false,

    "multi_proc": true,
    "multi_proc_cpu": 4,

    "multi_thread": true,
    "multi_thread_workers": 10
}
```

| Parameter                | Description                                                |
|--------------------------|------------------------------------------------------------|
| **xnat_server**          | xnat host name                                             |
| **xnat_user**            | xnat user                                                  |
| **xnat_password**        | xnat password                                              |
| **xnat_projects**        | xnat projects to be processed                              |
| **preprocess_functions** | preprocessing functions to run                             |
| **index**                | enables comparing local database and xnat to add new scans |
| **reset**                | overwrites previously generated output                     |
| **multi_proc**           | enables multi-processing                                   |
| **multi_proc_cpu**       | number of cpus to use in multi-processing                  |
| **multi_thread**         | enables multi-threading (within each process)              |
| **multi_thread_workers** | number of pool workers for multi-threading                 |



xnat_tools

This module contains basic functions for interacting with XNAT.

All data from the 


quality_tools




