This folder contains compose file to spin up a Samba share on localhost. Assumes placement of `shared` directory as follows:

```
.                           <- vm dir
├── smb
│   └── docker-compose.yml  <- this file
├── shared                  <- directory that will be shared
│   ├── ...
│   └── ...
├── vmconfig.yml
└── ...
```
