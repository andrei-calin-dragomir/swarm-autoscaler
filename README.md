# swarm-autoscaler
Container autoscaler for docker swarm stacks.

## Autoscaler (Work in progress)
This autoscaler makes use of the data sourced from CAdvisor and provides automated scaling based on the following parameters:
- CPU Utilization

**Autoscaling service configuration**
- `DATABASE_URL`: URL of the database from which the autoscaler scrapes relevant data
- `INFLUXDB_TOKEN` : Token to enable access to the database
- `INFLUXDB_ORG`: 'greenlab'
- `POLLING_FREQ`: At what frequency to update scales (in minutes)
- `SCALE_UP_THRESHOLD` : CPU utilization at which to try scaling a service up (in percentages)
- `SCALE_DOWN_THRESHOLD` : CPU utilization at which to try scaling a service down (in percentages)
- `SCALABLE_STACK`: Name of the stack to apply scaling to

**Scalable Service Configuration**
In order for this autoscaler to work the following requirements must be met:
- Autoscaler must be deployed on a `manager` node;
- Each service that should be scaled should be deployed with these labels:
  - `swarm.autoscaler: 'true'` (Enables autoscaler administration)
  - `swarm.autoscaler.maximum: '4'` (Sets the maximum number of replicas allowed)
  - `swarm.autoscaler.minimum: '2'` (Sets the minimum number of replicas allowed)

Docker compose configuration entry example:
```docker
scalable-service:
    ...
    deploy:
        labels:
            swarm.autoscaler: 'true'
            swarm.autoscaler.maximum: '4'
            swarm.autoscaler.minimum: '2'
```

## Deployment

### Stand-alone version
This deploys the autoscaler with the services it requires to gather data.

### Plug-and-play version
This deploys the autoscaler attaching it to an already existing data source for CAdvisor metrics (or other data sources)

1. Fill up your own configuration in the docker-compose.yml
2. `docker-compose build autoscaler`
3. `docker-compose up autoscaler`

