variable "instance_name" {
  description = "Name of the Week 7 virtual machine"
  type        = string
  default     = "week7-iac-vm"
}

variable "image_name" {
  description = "Ubuntu image available in cPouta"
  type        = string
  default     = "Ubuntu-24.04"
}

variable "flavor_name" {
  description = "Compute flavor for the virtual machine"
  type        = string
  default     = "standard.small"
}

variable "key_pair_name" {
  description = "Existing SSH key pair in cPouta"
  type        = string
  default     = "cloud-services-key"
}

variable "security_group_name" {
  description = "Security group to attach to the virtual machine"
  type        = string
  default     = "week7-iac-security"
}

variable "network_name" {
  description = "Private network for the virtual machine"
  type        = string
  default     = "project_2020498"
}
