# MCP-ML-PIPELINE 🚀  
*A Self-Healing CI/CD Pipeline with Model-Centric Approach*

MCP-ML-PIPELINE is a **self-healing CI/CD pipeline** designed to automate deployment, monitoring, and recovery of ML models and applications.  
It brings together **Jenkins, Kubernetes, Prometheus, Grafana, and an MCP (Model-Centric Pipeline) server** to build a resilient system that detects, analyzes, and fixes failures at runtime.  

---

## 🚀 Features  

- 🤖 **Self-Healing Pods**: Detects and recovers from crashes, misconfigurations, or runtime errors.  
- 🔍 **Failure Analysis**: Uses Vertex AI (Gemini) and rule-based logic for actionable healing recommendations.  
- 📊 **Observability**: Integrated with Prometheus & Grafana dashboards for metrics and alerts.  
- ⚡ **CI/CD Ready**: Jenkins pipeline for automated build → push → deploy.  
- 🛠 **Kubernetes-Native**: Deploys workloads and MCP as microservices in a cluster.  

## ⚙️ Installation & Setup

- **Clone the Repository
- **Build docker Image from the /mcp and deploy mcp server
- **Build docker Image from root for your app
- **Deploy your app kuberenetes deployment and then setup your monitoring deployments as well from the /k8s.

## 🔄 Self-Healing Workflow

- Pods generate logs and errors.
- MCP server captures logs from Kubernetes API.
- Errors are analyzed with rule-based + LLM-assisted logic.
- Healing directives applied (restart pod, inject dependencies, fix configs).
- All healing actions stored in healing_logs/ for continuous improvement.

## 🚀 Future Improvements

- 📝 Train a domain-specific ML model from healing logs.
- 🌎 Extend healing to service-level failures.
- 🔄 Plug in different LLMs (local or cloud APIs).
- ⚡ Full Jenkins integration with healing feedback loop.

🤝 Contributions are welcome!
