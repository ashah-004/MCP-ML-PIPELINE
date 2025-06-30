from transformers import RobertaTokenizer, RobertaForSequenceClassification
import torch

# Force use of the same tokenizer as training
tokenizer = RobertaTokenizer.from_pretrained("roberta-base")

# Load model from saved directory
model = RobertaForSequenceClassification.from_pretrained("app/model")
model.eval()

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def predict(text: str, temperature: float = 2.0, threshold: float = 0.6) -> dict:
    # Tokenize input
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Predict logits
    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits

    # Apply temperature scaling
    scaled_logits = logits / temperature
    probs = torch.softmax(scaled_logits, dim=-1).cpu().numpy()[0]

    # Prediction using threshold
    pred = int(probs[1] > threshold)

    return {
        "prediction": pred,  # 0 = Human, 1 = AI
        "confidence": float(probs[pred]),
        "probabilities": {"human": float(probs[0]), "ai": float(probs[1])}
    }


# Your Kubernetes control-plane has initialized successfully!

# To start using your cluster, you need to run the following as a regular user:

#   mkdir -p $HOME/.kube
#   sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
#   sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Alternatively, if you are the root user, you can run:

#   export KUBECONFIG=/etc/kubernetes/admin.conf

# You should now deploy a pod network to the cluster.
# Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
#   https://kubernetes.io/docs/concepts/cluster-administration/addons/

# You can now join any number of control-plane nodes by copying certificate authorities
# and service account keys on each node and then running the following as root:

#   kubeadm join 10.168.0.3:6443 --token jbvalk.pif14f5gwqcgbyue \
#         --discovery-token-ca-cert-hash sha256:6f441ec811eb78ef2e193d38c23b8b7c13aed2615fad1010d9e2e85befc09736 \
#         --control-plane 

# Then you can join any number of worker nodes by running the following on each as root:

# kubeadm join 10.168.0.3:6443 --token jbvalk.pif14f5gwqcgbyue \
#         --discovery-token-ca-cert-hash sha256:6f441ec811eb78ef2e193d38c23b8b7c13aed2615fad1010d9e2e85befc09736 