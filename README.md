# swarm-autoscaler
Container autoscaler for docker swarm stacks based on CAdvisor metrics.

## Implementation
This autoscaler makes use of the data sourced from CAdvisor and provides automated scaling based on the following parameters:
- CPU Utilization

The service polls InfluxDB with the following query which provides the CPU usage percentages in the last `polling_freq` minutes:
```python
f"""
from(bucket: "{influxdb_bucket}")
  |> range(start: -{polling_freq}m, stop: now())
  |> filter(fn: (r) => r["_measurement"] == "container_cpu_usage_seconds_total")
  |> filter(fn: (r) => r["_field"] == "counter")
  |> difference(nonNegative: true) // Calculate the per-second change
  |> map(fn: (r) => ({{ 
    r with _value: (r._value / {polling_freq * 60.0}) * 100.0 // Convert to rate per second and scale
  }}))
  |> group(columns: ["container_label_com_docker_swarm_service_id"])
  |> sum() // Aggregate over the specified groups
"""
```

**Autoscaling service configuration**
- `DATABASE_URL`: URL of the database from which the autoscaler scrapes relevant data
- `INFLUXDB_TOKEN` : Token to enable access to the database
- `INFLUXDB_ORG`: 'greenlab'

- `DEFAULT_POLLING_FREQ`: At what frequency to read service CPU utilizations and update service replicas (in minutes)
- `DEFAULT_SCALE_UP_THRESHOLD` : CPU utilization at which to try scaling a service up (in percentages)
- `DEFAULT_SCALE_DOWN_THRESHOLD` : CPU utilization at which to try scaling a service down (in percentages)

### Scalable Service Configuration
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
This deploys the autoscaler attaching it to the [Monitoring Stack](https://github.com/vnzstc/swarm-monitoring.git) in order to extract the required data about the active nodes within the docker swarm.

1. Fill up your own configuration in the docker-compose.yml
2. `docker-compose build autoscaler`
3. `docker-compose up autoscaler`
