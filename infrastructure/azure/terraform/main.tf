# -------------------
# 1. Resource Group
# -------------------

resource "azurerm_resource_group" "rg" {
    name        = "${var.project_name}-rg"
    location    = var.location
}

# -------------------
# 2. Azure OpenAI (LLMs)
# -------------------

resource "azurerm_cognitive_account" "openai" {
    name                    = "${var.project_name}-openai"
    location                = azurerm_resource_group.rg.location
    resource_group_name     = azurerm_resource_group.rg.name
    kind                    = "OpenAI"
    sku_name                = "S0"
}

# -------------------
# 3. Azure AI Search (RAG Index)
# -------------------

resource "azurerm_search_service" "search" {
    name                    = "${var.project_name}-search"
    resource_group_name     = azurerm_resource_group.rg.name
    location                = azurerm_resource_group.rg.location
    sku                     = "basic"
    partition_count         = 1
    replica_count           = 1
}

# -------------------
# 4. Blob Storage (Docs + Attachments)
# -------------------

resource "azurerm_storage_account" "storage" {
    name                        = "${var.project_name}storage"
    resource_group_name         = azurerm_resource_group.rg.name
    location                    = azurerm_resource_group.rg.location
    account_tier                = "Standard"
    account_replication_type    = "LRS"
}

resource "azurerm_storage_container" "blobs" {
    name                    = "attachments"
    storage_account_name    = azurerm_storage_account.storage.name
    container_access_type   = "private"
}

# -------------------
# 5. Key Vault (Secrets / API Keys)
# -------------------
data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "kv" {
    name                        = "${var.project_name}-kv"
    resource_group_name         = azurerm_resource_group.rg.name
    location                    = azurerm_resource_group.rg.location
    tenant_id                   = data.azurerm_client_config.current.tenant_id
    sku_name                    = "standard"
    purge_protection_enabled    = true
    soft_delete_retention_days  = 7

    lifecycle {
        ignore_changes = [contact]
    }
}

# -------------------
# 6. AKS Cluster (Agent Runtime)
# -------------------

resource "azurerm_kubernetes_cluster" "aks" {
    name                = "${var.project_name}-aks"
    location            = azurerm_resource_group.rg.location
    resource_group_name = azurerm_resource_group.rg.name
    dns_prefix          = "${var.project_name}-dns"

    default_node_pool {
        name        = "default"
        node_count  = 1
        vm_size     = "Standard_B4ms"
    }

    identity {
        type = "SystemAssigned"
    }

    network_profile {
        network_plugin = "azure"
    }
}

# -------------------
# 7. Monitoring
# -------------------

resource "azurerm_log_analytics_workspace" "logs" {
    name                    = "${var.project_name}-logs"
    location                = azurerm_resource_group.rg.location
    resource_group_name     = azurerm_resource_group.rg.name
    sku                     = "PerGB2018"
    retention_in_days       = 30
}

resource "azurerm_monitor_diagnostic_setting" "diag" {
    name                        = "${var.project_name}-diag"
    target_resource_id          = azurerm_kubernetes_cluster.aks.id
    log_analytics_workspace_id  = azurerm_log_analytics_workspace.logs.id

    log {
        category = "kube-apiserver"
        enabled = true
    }
}