# from kubernetes import client, config
# from kubernetes.client.rest import ApiException
# import base64
# import logging

# # Load in-cluster config automatically when running inside K8s pod
# try:
#     config.load_incluster_config()
# except:
#     config.load_kube_config()

# core_v1 = client.CoreV1Api()
# apps_v1 = client.AppsV1Api()

# def get_pod_logs(namespace: str, pod_name: str, container: str = None, tail_lines: int = 1000) -> str:
#     try:
#         return core_v1.read_namespaced_pod_log(
#             name=pod_name,
#             namespace=namespace,
#             container=container,
#             tail_lines=tail_lines,
#             _preload_content=True
#         )
#     except ApiException as e:
#         logging.error(f"Error fetching logs for pod {pod_name} in {namespace}: {e}")
#         return ""

# def patch_deployment(namespace: str, deployment_name: str, patch: dict) -> bool:
#     try:
#         apps_v1.patch_namespaced_deployment(
#             name=deployment_name,
#             namespace=namespace,
#             body=patch
#         )
#         return True
#     except ApiException as e:
#         logging.error(f"Error patching deployment {deployment_name} in {namespace}: {e}")
#         return False

# def restart_deployment(namespace: str, deployment_name: str) -> bool:
#     # Restart by patching an annotation with current timestamp (forces pods to restart)
#     import datetime
#     patch = {
#         "spec": {
#             "template": {
#                 "metadata": {
#                     "annotations": {
#                         "mcp-restarted-at": datetime.datetime.utcnow().isoformat()
#                     }
#                 }
#             }
#         }
#     }
#     return patch_deployment(namespace, deployment_name, patch)
from kubernetes import client, config
from kubernetes.stream import stream
from kubernetes.client.rest import ApiException
import logging
import time

try:
    config.load_incluster_config()
except Exception:
    config.load_kube_config()

core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

def wait_for_pod_ready(namespace: str, pod_name: str, timeout=60):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            conditions = pod.status.conditions or []
            ready_conditions = [c for c in conditions if c.type == "Ready" and c.status == "True"]
            if pod.status.phase == "Running" and ready_conditions:
                return True
        except ApiException:
            pass
        time.sleep(3)
    return False

def wait_for_container_ready(namespace: str, pod_name: str, expected_container: str, timeout=15):
    for _ in range(timeout):
        try:
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            container_names = [c.name for c in pod.spec.containers]
            if expected_container in container_names:
                return True
        except ApiException:
            pass
        time.sleep(1)
    raise RuntimeError(f"[MCP] Container '{expected_container}' not ready in pod '{pod_name}' after {timeout}s")

def get_pod_logs(namespace: str, pod_name: str, container: str = None, tail_lines: int = 1000) -> str:
    try:
        return core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines
        )
    except ApiException as e:
        logging.error(f"[MCP] Error fetching logs for pod {pod_name} in {namespace}: {e}")
        return ""

def patch_deployment(namespace: str, deployment_name: str, patch: dict) -> bool:
    try:
        apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=patch)
        return True
    except ApiException as e:
        logging.error(f"[MCP] Error patching deployment {deployment_name}: {e}")
        return False

def restart_deployment(namespace: str, deployment_name: str) -> bool:
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

def find_target_pod(namespace: str, deployment_name: str) -> str:
    try:
        pods = core_v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=f'app={deployment_name}'
        )
        for pod in pods.items:
            if pod.status.phase == "Running":
                return pod.metadata.name
        return pods.items[0].metadata.name if pods.items else ""
    except Exception as e:
        logging.error(f"[MCP] Error finding pod for deployment {deployment_name}: {e}")
        return ""

MAX_RETRIES = 3
RETRY_DELAY = 3

def exec_command_in_pod(namespace: str, pod_name: str, command: str):
    try:
        pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
        containers = [c.name for c in pod.spec.containers]
        container_name = containers[0]
        print(f"[MCP] Detected containers in pod: {containers}")

        # Add container readiness wait
        wait_for_container_ready(namespace, pod_name, container_name)

    except Exception as e:
        logging.error(f"[MCP] Failed to retrieve pod/container info: {e}")
        return {
            "success": False,
            "output": f"Error retrieving pod/container info: {e}"
        }

    exec_command = ["/bin/sh", "-c", command]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[MCP] Attempt {attempt}: executing `{command}` in pod `{pod_name}` (container={container_name})")
            resp = stream(
                core_v1.connect_get_namespaced_pod_exec,
                name=pod_name,
                namespace=namespace,
                container=container_name,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )
            print(f"[MCP] Exec success: {command}")
            return {
                "success": True,
                "output": resp
            }

        except ApiException as e:
            print(f"[MCP] Exec attempt {attempt} failed: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return {
                    "success": False,
                    "output": f"Exec failed after {MAX_RETRIES} attempts: {e}"
                }
        except Exception as e:
            print(f"[MCP] Unexpected error: {e}")
            return {
                "success": False,
                "output": f"Unexpected error during exec: {e}"
            }

