output "resource_group_name" {
    description = "The name of the Azure Resource Group"
    value = azurerm_resource_group.rg.name
}

output "openai_endpoint" {
    value = azurerm_cognitive_account.openai.endpoint
}

output "search_service_name" {
    description = "The name of the Azure Cognitive Search service"
    value = azurerm_search_service.search.name
}

output "storage_account_name" {
    value = azurerm_storage_account.storage.name
}

output "key_vault_uri" {
    description = "The URI of the Azure Key Vault"
    value = azurerm_key_vault.kv.vault_uri
}

output "key_vault_id" {
    description = "The resource ID of the Key Vault"
    value = azurerm_key_vault.kv.id
}