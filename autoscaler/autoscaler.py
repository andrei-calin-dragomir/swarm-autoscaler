import os
import time
import influxdb_client
from typing import List
from python_on_whales import docker, Service

# Retrieve environment variables
influxdb_url = os.getenv('INFLUXDB_URL')
influxdb_bucket = os.getenv("INFLUXDB_BUCKET")
influxdb_org = os.getenv('INFLUXDB_ORG')
influxdb_token = os.getenv("INFLUXDB_TOKEN")

polling_freq = int(os.getenv('DEFAULT_POLLING_FREQ'))
scale_up_thold = int(os.getenv('DEFAULT_SCALE_UP_THRESHOLD'))
scale_down_thold = int(os.getenv('DEFAULT_SCALE_DOWN_THRESHOLD'))

# Initialize DB client
db_client = influxdb_client.InfluxDBClient(url=influxdb_url, token=influxdb_token, org=influxdb_org)
db_query_client = db_client.query_api()

# Query for CPU utilization of all active services
cpu_util_data_query = f"""
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

# List of scalable services
scalable_services : List[Service] = []

# Returns a list of lists of form:
# [
#   [cpu_percentage : float, service_id : string]
# ]
def query_service_cpu_util() -> List[List[object]]:
    try:
        data = db_query_client.query(cpu_util_data_query)
        if data:
            print("API query successful")
            stats : List[List[object]] = data.to_values(columns=["_value", "container_label_com_docker_swarm_service_id"])
            return stats
        else:
            print("API query failed")
            return None
    except Exception as e:
        print(f"Error querying API: {str(e)}")
        return None

def get_service_info(service: Service):
    replica_minimum = int(service.spec.labels.get('swarm.autoscaler.minimum', 1))
    replica_maximum = int(service.spec.labels.get('swarm.autoscaler.maximum', 1))
    current_replicas = int(service.spec.mode['Replicated']['Replicas'])
    return replica_minimum, replica_maximum, current_replicas

def get_scalable_services() -> List[Service]:
    services : List[Service] = docker.service.list()

    # List to hold the scalable services for the current stack
    scalable_services = []

    for service in services:
        # Check if the service has the swarm.autoscaler label set to true
        labels = docker.service.inspect(service.id).spec.labels
        if labels.get('swarm.autoscaler', 'false') == 'true':
            scalable_services.append(service)

    return scalable_services

def align_services_with_specs():
    for service in scalable_services:
        replica_minimum, _, current_replicas = get_service_info(service)
        if current_replicas != replica_minimum:
            print(f'Scaling service {service.spec.name} to {replica_minimum} replicas.')
            docker.service.scale({service: replica_minimum})

def scale_from_cpu_util(services_data : List[List[object]]):
    for service_data in services_data:
        service_id = service_data[1]
        service_utilization = service_data[0]
        for service in scalable_services:
            if service.id == service_id:
                replica_minimum, replica_maximum, current_replicas = get_service_info(service)
                print(f'Service {service.__name__} is being analysed.')
                if service_utilization >= scale_up_thold and current_replicas < replica_maximum:
                    docker.service.scale({service: current_replicas + 1})
                elif service_utilization <= scale_down_thold and current_replicas > replica_minimum:
                    docker.service.scale({service: current_replicas - 1})
                break

if __name__ == "__main__":
    scalable_services = get_scalable_services()
    align_services_with_specs()
    while True:
        stats = query_service_cpu_util()
        if stats:
            scale_from_cpu_util(stats)
        else:
            print("Failed to retrieve required data... (Check db query/status)")
        time.sleep(polling_freq)
