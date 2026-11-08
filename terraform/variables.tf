variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "instance_type" {
  description = "EC2 size. t3.micro is free-tier eligible in most accounts."
  type        = string
  default     = "t3.micro"
}

variable "my_ip_cidr" {
  description = "Your public IP in CIDR form (e.g. 203.0.113.7/32). Only this IP can SSH in."
  type        = string
}

variable "ssh_key_name" {
  description = "Name of an existing EC2 key pair for SSH access"
  type        = string
}

variable "image" {
  description = "Container image to run"
  type        = string
  default     = "ghcr.io/cnweke3506/taskboard:latest"
}
