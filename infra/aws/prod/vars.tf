variable "api_key" {
  description = "API key for accessing API endpoints"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
  default     = "prod"
}
