# ── AWS Region ────────────────────────────────────────────────────────────────
variable "aws_region" {
  description = "AWS region where all resources will be created"
  type        = string
  default     = "us-east-1"
}

# ── Project Info ──────────────────────────────────────────────────────────────
variable "project_name" {
  description = "Short name for the project, used in resource names and tags"
  type        = string
  default     = "cart-api"
}

variable "environment" {
  description = "Deployment environment (dev / staging / prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "environment must be one of: dev, staging, prod"
  }
}

# ── EC2 ───────────────────────────────────────────────────────────────────────
variable "ami_id" {
  description = "Amazon Machine Image ID. Default is Amazon Linux 2023 in eu-north-1"
  type        = string
  default     = "ami-0c1ac1a84c78a5ed2" # Amazon Linux 2023 — eu-north-1
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"

  validation {
    condition     = contains(["t3.micro", "t3.small", "t3.medium", "t3.large"], var.instance_type)
    error_message = "instance_type must be one of: t3.micro, t3.small, t3.medium, t3.large"
  }
}

variable "key_name" {
  description = "Name of the AWS Key Pair to use for SSH access to the EC2 instance"
  type        = string
  # No default — you must supply this. It is the key pair name in AWS Console.
}

variable "root_volume_size_gb" {
  description = "Size of the root EBS volume in gigabytes"
  type        = number
  default     = 20
}

# ── Networking ────────────────────────────────────────────────────────────────
variable "vpc_id" {
  description = "VPC ID to launch the EC2 instance in. Leave empty to use the default VPC"
  type        = string
  default     = "" # empty = use default VPC
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed to SSH into the EC2 instance. Change to your own IP for security"
  type        = string
  default     = "0.0.0.0/0" # open to all — restrict to your IP in production
}

# ── Remote State ──────────────────────────────────────────────────────────────
variable "state_bucket_name" {
  description = "S3 bucket name where Terraform state is stored"
  type        = string
  default     = "cart-api-terraform-state"
}

variable "state_lock_table" {
  description = "DynamoDB table name used for Terraform state locking"
  type        = string
  default     = "cart-api-terraform-locks"
}

# ── Existing Infrastructure ───────────────────────────────────────────────────
variable "existing_instance_id" {
  description = "If you already have an EC2 instance, put its ID here to import it instead of creating a new one. Leave empty to create new."
  type        = string
  default     = ""
}
