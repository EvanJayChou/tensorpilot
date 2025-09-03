# Terraform Deployment for TensorPilot

This folder contains Terraform scripts to provision core Azure resources for the TensorPilot project.

## Prerequisites

1. **Azure Account**: Make sure you have an active Azure subscription.
2. **Azure CLI**: Install [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) and log in:
    ```powershell
    az login
    ```
3. **Terraform**: Installed and added to PATH (verify with `terraform version`).
4. **Service Principal (Optional)**: For CI/CD automation:
    ```powershell
    az ad sp create-for-rbac --name "terraform-sp-math" --role="Contributor" --scopes="/subscriptions/<SUBSCRIPTION_ID>"
    ```

---

## Folder Structure
```
terraform/
├─ main.tf # Resource definitions
├─ variables.tf # Variables like project name, location
├─ outputs.tf # Captures endpoints and key vault URI
├─ providers.tf # Azure provider configuration
└─ README.md
```

---

## Quick Start (Local Dev)

1. **Clone the repo and navigate to terraform folder**
```powershell
cd infrastructure/azure/terraform
```

2. **Initialize Terraform**
```powershell
terraform init
```

3. **Plan changes**
```powershell
terraform plan
```

4. **Apply changes**
```powershell
terraform apply
```

- Confirm with `yes` when prompted.
- This will provision:
    - Resource Group
    - Azure Cognitive Search
    - Azure Key Vault

5. **View outputs**
```powershell
terraform output
```

You will see:
- Resource Group name
- Search service endpoint
- Key Vault URI