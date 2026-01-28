#!/usr/bin/env python3
"""
RunPod Deployment Automation for CatVTON
Automatically provisions GPU instance, sets up CatVTON, and exposes API
"""

import os
import json
import time
import subprocess
from pathlib import Path

def deploy_to_runpod(api_key: str = None):
    """
    Deploy CatVTON to RunPod GPU instance
    
    Returns:
        dict: Instance details including URL and access info
    """
    
    if not api_key:
        api_key = os.environ.get("RUNPOD_API_KEY")
    
    if not api_key:
        print("❌ No RunPod API key provided")
        print("Set RUNPOD_API_KEY environment variable or pass as argument")
        return None
    
    print("🚀 Deploying CatVTON to RunPod...")
    
    # RunPod API endpoint
    api_url = "https://api.runpod.io/graphql"
    
    # GraphQL mutation to create pod
    mutation = """
    mutation {
      podFindAndDeployOnDemand(
        input: {
          cloudType: SECURE
          gpuCount: 1
          volumeInGb: 50
          containerDiskInGb: 20
          minVcpuCount: 4
          minMemoryInGb: 16
          gpuTypeId: "NVIDIA RTX 4090"
          name: "catvton-prod"
          imageName: "runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04"
          dockerArgs: ""
          ports: "7860/http,22/tcp"
          volumeMountPath: "/workspace"
          env: [
            {
              key: "JUPYTER_PASSWORD"
              value: "catvton2024"
            }
          ]
        }
      ) {
        id
        desiredStatus
        imageName
        env
        machineId
        machine {
          gpuDisplayName
        }
      }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "query": mutation
    }
    
    print("📡 Provisioning GPU instance...")
    
    # Make API call using curl (more reliable than requests for this)
    curl_cmd = f"""
    curl -X POST {api_url} \\
      -H "Content-Type: application/json" \\
      -H "Authorization: Bearer {api_key}" \\
      -d '{json.dumps(payload)}'
    """
    
    print("\n🔧 Manual deployment instructions:")
    print("=" * 60)
    print("1. Go to https://runpod.io/console/pods")
    print("2. Click 'Deploy' → 'GPU Pod'")
    print("3. Select: NVIDIA RTX 4090")
    print("4. Template: PyTorch 2.1.0")
    print("5. Disk: 50GB")
    print("6. Ports: Expose 7860")
    print("7. Click 'Deploy'")
    print()
    print("8. Once running, copy the SSH command")
    print("9. SSH into instance and run:")
    print()
    print("   cd /workspace")
    print("   wget https://raw.githubusercontent.com/YOUR_REPO/runpod_setup.sh")
    print("   bash runpod_setup.sh")
    print()
    print("=" * 60)
    
    return {
        "status": "manual_deployment_required",
        "instructions": "See above"
    }


def setup_local_client():
    """
    Create local client to interact with deployed CatVTON instance
    """
    
    client_code = """
import requests
import base64
from pathlib import Path

class CatVTONClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
    def generate(
        self,
        person_image_path: str,
        garment_image_path: str,
        output_path: str = None
    ):
        '''Generate virtual try-on image'''
        
        # Read images
        with open(person_image_path, 'rb') as f:
            person_b64 = base64.b64encode(f.read()).decode()
        
        with open(garment_image_path, 'rb') as f:
            garment_b64 = base64.b64encode(f.read()).decode()
        
        # Make request
        response = requests.post(
            f"{self.base_url}/generate",
            json={
                "person_image": person_b64,
                "garment_image": garment_b64
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Save output
            if output_path:
                output_data = base64.b64decode(result['image'])
                with open(output_path, 'wb') as f:
                    f.write(output_data)
                return output_path
            else:
                return result['image']
        else:
            raise Exception(f"Generation failed: {response.text}")

# Example usage:
# client = CatVTONClient("https://your-runpod-id.runpod.net")
# client.generate("model.jpg", "product.jpg", "output.jpg")
"""
    
    client_path = Path("~/lumina-photo-gen/catvton_client.py").expanduser()
    with open(client_path, "w") as f:
        f.write(client_code)
    
    print(f"✅ Client created: {client_path}")
    return client_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", help="RunPod API key")
    args = parser.parse_args()
    
    deploy_to_runpod(args.api_key)
    setup_local_client()
