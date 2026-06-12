# Requirements Document

## Introduction

This document defines the requirements for implementing Infrastructure as Code (IaC) using Terraform for the FastAPI Cart API project. Currently, the project runs on an AWS EC2 instance with Docker and docker-compose, uses PostgreSQL (`cartdb`), Nginx as a reverse proxy, and deploys via a blue/green deployment strategy through GitHub Actions.

**What is IaC and why do we need it?**

Infrastructure as Code (IaC) means describing your cloud infrastructure (servers, databases, networking, security groups, etc.) in code files that can be version-controlled, reviewed, and automatically applied — the same way you manage application code. Without IaC, the EC2 instance, security groups, key pairs, and networking were likely created manually through the AWS Console. This is fragile: if the instance is lost or needs to be reproduced in another region, the setup steps exist only in someone's memory. Terraform solves this by letting you declare the desired state of your AWS infrastructure in `.tf` files. Running `terraform apply` creates or updates resources to match that state, and `terraform destroy` tears them all down cleanly.

The goal of this feature is to codify all the AWS infrastructure that supports the Cart API into Terraform, store it under a `terraform/` directory in the project repository, and integrate it with the existing GitHub Actions CI/CD workflows.

## Glossary

- **Terraform**: An open-source IaC tool by HashiCorp that provisions cloud infrastructure from declarative configuration files.
- **Provider**: A Terraform plugin that manages a specific cloud platform (e.g., `hashicorp/aws`).
- **Resource**: A piece of infrastructure managed by Terraform (e.g., `aws_instance`, `aws_security_group`).
- **State**: A file (local or remote) that records the current known state of managed infrastructure.
- **Remote State**: Terraform state stored in a shared backend (e.g., AWS S3) rather than on a local machine.
- **State Lock**: A mechanism (e.g., DynamoDB table) that prevents concurrent `terraform apply` runs from corrupting state.
- **Workspace**: A Terraform concept for managing multiple environments (e.g., `dev`, `prod`) from the same configuration.
- **EC2_Instance**: The AWS Elastic Compute Cloud virtual machine that hosts the Cart API Docker containers and Nginx.
- **Security_Group**: An AWS virtual firewall that controls inbound and outbound traffic to the EC2_Instance.
- **Key_Pair**: An AWS SSH key pair used to authenticate connections to the EC2_Instance.
- **Elastic_IP**: A static public IP address assigned to the EC2_Instance so its address does not change on restart.
- **S3_Backend**: An AWS S3 bucket used to store Terraform remote state.
- **DynamoDB_Lock_Table**: An AWS DynamoDB table used to implement Terraform state locking.
- **User_Data**: A startup script passed to an EC2_Instance at launch time that installs Docker, Nginx, and other dependencies.
- **Nginx**: The reverse proxy running on the EC2_Instance that routes traffic to either the blue or green container.
- **Blue_Container**: The Docker container running the Cart API on port 8001.
- **Green_Container**: The Docker container running the Cart API on port 8002.
- **Terraform_Module**: A reusable, self-contained package of Terraform configuration.
- **tfvars_File**: A file (e.g., `terraform.tfvars`) that supplies variable values to a Terraform configuration.
- **Output**: A Terraform-declared value (e.g., public IP) exposed after `terraform apply` completes.
- **IAM_Role**: An AWS Identity and Access Management role that grants the EC2_Instance permissions to interact with AWS services.

---

## Requirements

### Requirement 1: Terraform Project Structure

**User Story:** As a developer, I want a well-organized Terraform directory in the project repository, so that the infrastructure code is easy to navigate, review, and maintain alongside application code.

#### Acceptance Criteria

1. THE Terraform_Module SHALL be placed in a `terraform/` directory at the root of the project repository.
2. THE Terraform_Module SHALL separate concerns across these files: `main.tf` (provider and top-level resources), `variables.tf` (input variable declarations), `outputs.tf` (output declarations), `terraform.tfvars` (default variable values), and `versions.tf` (required provider and Terraform version constraints).
3. THE Terraform_Module SHALL include a `README.md` inside the `terraform/` directory that documents how to initialize, plan, and apply the configuration.
4. THE `terraform/` directory SHALL include a `.gitignore` file that excludes `.terraform/`, `*.tfstate`, `*.tfstate.backup`, and `*.tfvars` containing secrets from version control.

---

### Requirement 2: AWS Provider Configuration

**User Story:** As a developer, I want Terraform to be configured with the AWS provider and version constraints, so that the infrastructure can be provisioned reproducibly against the correct provider version.

#### Acceptance Criteria

1. THE Terraform_Module SHALL declare the `hashicorp/aws` provider with a minimum version constraint of `~> 5.0`.
2. THE Terraform_Module SHALL declare a minimum Terraform version constraint of `>= 1.5.0`.
3. THE Terraform_Module SHALL accept an `aws_region` input variable with a default value of `"us-east-1"` that configures the AWS provider region.
4. WHEN no explicit AWS credentials are provided in the configuration, THE Terraform_Module SHALL rely on the standard AWS credential chain (environment variables, shared credentials file, or IAM instance profile).
5. IF the AWS credential chain is unavailable or fails to authenticate, THEN THE Terraform_Module SHALL terminate immediately and emit a descriptive error message identifying that valid AWS credentials could not be found.

---

### Requirement 3: Remote State Backend

**User Story:** As a developer, I want Terraform state stored remotely in S3 with locking, so that multiple team members and CI/CD pipelines can safely apply infrastructure changes without state conflicts.

#### Acceptance Criteria

1. THE Terraform_Module SHALL configure an S3 backend to store the Terraform state file in the S3_Backend bucket.
2. THE S3_Backend bucket SHALL have versioning enabled so that previous state revisions can be recovered.
3. THE S3_Backend bucket SHALL have server-side encryption enabled using AES-256.
4. THE Terraform_Module SHALL configure the DynamoDB_Lock_Table for state locking using a table with partition key `LockID` of type String.
5. THE `terraform/` directory SHALL include a `backend.tf` file or inline backend block that declares the S3 backend configuration using variables for bucket name and DynamoDB table name.
6. THE `terraform/` directory SHALL include a `bootstrap/` sub-directory containing a standalone Terraform configuration that creates the S3_Backend bucket and DynamoDB_Lock_Table as a one-time setup step.

---

### Requirement 4: Networking and Security Groups

**User Story:** As a developer, I want Terraform to manage the VPC networking and security group rules for the EC2 instance, so that the firewall configuration is auditable and reproducible.

#### Acceptance Criteria

1. THE Terraform_Module SHALL use the default AWS VPC and subnets unless an explicit `vpc_id` variable is provided.
2. THE Terraform_Module SHALL create a Security_Group named `cart-api-sg` that allows inbound TCP traffic on port 22 (SSH) from a configurable CIDR block variable `ssh_allowed_cidr` with default `"0.0.0.0/0"`.
3. THE Security_Group SHALL allow inbound TCP traffic on port 80 (HTTP) from `"0.0.0.0/0"`.
4. THE Security_Group SHALL allow inbound TCP traffic on port 443 (HTTPS) from `"0.0.0.0/0"`.
5. THE Security_Group SHALL allow all outbound traffic to `"0.0.0.0/0"`.
6. WHEN a `restrict_ssh` variable is set to `true`, THE Terraform_Module SHALL restrict SSH inbound access to only the CIDR block supplied in `ssh_allowed_cidr`.

---

### Requirement 5: EC2 Instance Provisioning

**User Story:** As a developer, I want Terraform to provision the EC2 instance that runs the Cart API, so that the server can be reproduced identically from code if it is ever terminated or needs to be scaled.

#### Acceptance Criteria

1. THE Terraform_Module SHALL create an EC2_Instance resource using an input variable `ami_id` with a default Amazon Linux 2023 AMI ID for `us-east-1`.
2. THE Terraform_Module SHALL accept an `instance_type` input variable with a default value of `"t3.micro"`.
3. THE EC2_Instance SHALL be associated with the Security_Group created in Requirement 4.
4. THE EC2_Instance SHALL be associated with the Key_Pair referenced by a `key_name` input variable.
5. THE EC2_Instance SHALL be assigned a root EBS volume with a configurable size variable `root_volume_size_gb` defaulting to `20` gigabytes and type `gp3`.
6. THE EC2_Instance SHALL receive a User_Data script that installs Docker, Docker Compose, Git, and Nginx on first boot.
7. THE User_Data script SHALL enable and start the Docker service and the Nginx service so that the EC2_Instance is ready to run the Cart API containers immediately after launch.
8. THE Terraform_Module SHALL tag the EC2_Instance with at minimum `Name`, `Environment`, and `Project` tags using input variables.

---

### Requirement 6: Elastic IP Assignment

**User Story:** As a developer, I want the EC2 instance to have a static public IP address managed by Terraform, so that the DNS record and GitHub Actions secrets do not need to change when the instance is restarted.

#### Acceptance Criteria

1. THE Terraform_Module SHALL create an Elastic_IP resource and associate it with the EC2_Instance.
2. THE Terraform_Module SHALL expose the Elastic_IP address as a Terraform Output named `ec2_public_ip`.
3. WHEN the EC2_Instance is stopped and restarted, THE Elastic_IP SHALL remain associated with the instance at the infrastructure level, and any additional manual steps required to restore full application functionality are acceptable.

---

### Requirement 7: IAM Role for EC2

**User Story:** As a developer, I want the EC2 instance to have an IAM role attached, so that it can interact with AWS services (such as pulling secrets from SSM Parameter Store) without requiring hardcoded AWS credentials on the server.

#### Acceptance Criteria

1. THE Terraform_Module SHALL create an IAM_Role named `cart-api-ec2-role` with an EC2 assume-role trust policy.
2. THE Terraform_Module SHALL create an IAM instance profile that attaches the IAM_Role to the EC2_Instance.
3. THE IAM_Role SHALL include a policy allowing `ssm:GetParameter` and `ssm:GetParameters` on parameter paths prefixed with `/cart-api/`.
4. THE IAM_Role SHALL include the `AmazonSSMManagedInstanceCore` managed policy to enable AWS Systems Manager Session Manager access as an alternative to SSH.

---

### Requirement 8: Input Variables and Outputs

**User Story:** As a developer, I want all configurable values declared as Terraform input variables with descriptions and types, so that the module can be reused across environments without editing the core configuration files.

#### Acceptance Criteria

1. THE `variables.tf` file SHALL declare every configurable value as a variable with a `description` and explicit `type`.
2. THE Terraform_Module SHALL expose at minimum these outputs in `outputs.tf`: `ec2_public_ip` (the Elastic_IP address), `ec2_instance_id` (the instance resource ID), and `security_group_id` (the Security_Group ID).
3. WHEN a required variable has no default value and is not supplied, THE Terraform_Module SHALL produce a descriptive validation error identifying the missing variable name.
4. THE Terraform_Module SHALL use variable validation blocks to reject an `instance_type` value that is not in the list `["t3.micro", "t3.small", "t3.medium", "t3.large"]`.

---

### Requirement 9: Integration with GitHub Actions

**User Story:** As a developer, I want the existing GitHub Actions workflows updated to use the Terraform-managed infrastructure details, so that deployments reference the Elastic IP from Terraform outputs rather than hardcoded values.

#### Acceptance Criteria

1. THE `terraform/` directory SHALL include a `terraform-plan.yml` GitHub Actions workflow file that runs `terraform fmt -check`, `terraform validate`, and `terraform plan` on every pull request to `main`.
2. THE `terraform-plan.yml` workflow SHALL authenticate to AWS using `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` GitHub Actions secrets.
3. THE `terraform-plan.yml` workflow SHALL post the `terraform plan` output as a pull request comment.
4. THE `terraform/` directory SHALL include a `terraform-apply.yml` GitHub Actions workflow file that runs `terraform apply -auto-approve` on every push to the `main` branch, regardless of which files changed.
5. THE existing `deploy.yml` workflow SHALL be updated to retrieve the EC2 host from the `ec2_public_ip` Terraform output (stored as a GitHub Actions secret `EC2_HOST`) rather than relying on a manually set value.

---

### Requirement 10: Secrets and Sensitive Value Handling

**User Story:** As a developer, I want all sensitive values (database passwords, SSH keys) kept out of Terraform state and code, so that credentials are never accidentally exposed in version control or CI logs.

#### Acceptance Criteria

1. THE Terraform_Module SHALL NOT hardcode database passwords, SSH private keys, or API secrets in any `.tf` file.
2. THE Terraform_Module SHALL reference the database password via an AWS SSM Parameter Store parameter path (`/cart-api/db_password`) of type `SecureString`, retrieved at apply time using a `aws_ssm_parameter` data source.
3. THE `terraform.tfvars` file SHALL be listed in `.gitignore` so that local overrides containing sensitive values are never committed.
4. THE Terraform_Module SHALL mark the database password output or variable as `sensitive = true` so that Terraform suppresses it from CLI output.

---

### Requirement 11: Existing Infrastructure Import

**User Story:** As a developer, I want guidance on how to import the existing manually-created AWS resources into Terraform state, so that Terraform manages the current infrastructure without destroying and recreating it.

#### Acceptance Criteria

1. THE `terraform/README.md` SHALL include a section titled "Importing Existing Resources" that documents the `terraform import` commands for each resource (EC2 instance, Elastic IP, Security Group, Key Pair).
2. THE Terraform_Module SHALL declare an `import` block (Terraform 1.5+ syntax) for the existing EC2_Instance using a variable `existing_instance_id` that defaults to an empty string, so the import block is skipped when the variable is not set.
3. WHEN `existing_instance_id` is set, THE Terraform_Module SHALL import the existing EC2_Instance into state rather than creating a new one.
