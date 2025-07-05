from kubernetes import client, config
from kubernetes.client.rest import ApiException
import base64
import logging

# Load in-cluster config automatically when running inside K8s pod
try:
    config.load_incluster_config()
except:
    config.load_kube_config()

core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

def get_pod_logs(namespace: str, pod_name: str, container: str = None, tail_lines: int = 1000) -> str:
    try:
        return core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
            _preload_content=True
        )
    except ApiException as e:
        logging.error(f"Error fetching logs for pod {pod_name} in {namespace}: {e}")
        return ""

def patch_deployment(namespace: str, deployment_name: str, patch: dict) -> bool:
    try:
        apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=patch
        )
        return True
    except ApiException as e:
        logging.error(f"Error patching deployment {deployment_name} in {namespace}: {e}")
        return False

def restart_deployment(namespace: str, deployment_name: str) -> bool:
    # Restart by patching an annotation with current timestamp (forces pods to restart)
    import datetime
    patch = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "mcp-restarted-at": datetime.datetime.utcnow().isoformat()
                    }
                }
            }
        }
    }
    return patch_deployment(namespace, deployment_name, patch)
