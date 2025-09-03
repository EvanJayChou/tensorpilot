variable "project_name" {
    type = string
    description = "Project name for resource naming"
    default = "tensorpilot"
}

variable "location" {
    type = string
    description = "Azure region for deployment"
    default = "westus"
}