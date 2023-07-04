**EuCanImage Image Preprocessing Toolkit**
------------------

This repository contains the code for preprocessing images for the EuCanImage project. 

Running the code requires a configuration file. An example configuration file is provided in the repository.


Configuration File
------------------

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




