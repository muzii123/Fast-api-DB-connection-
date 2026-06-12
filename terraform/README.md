# Cart API — Terraform Infrastructure

This directory contains all the Infrastructure as Code (IaC) for the Cart API project.
Running `terraform apply` here creates (or updates) all your AWS resources automatically.

---

## What Gets Created

| Resource | Description |
|---|---|
| `aws_security_group` | Firewall — opens ports 22, 80, 443, 8001, 8002 |
| `aws_iam_role` | Lets EC2 read secrets from SSM Parameter Store |
| `aws_instance` | EC2 server with Docker, Nginx pre-installed |
| `aws_eip` | Static public IP that never changes |

---

## Prerequisites

1. **Install Terraform** — [terraform.io/downloads](https://developer.hashicorp.com/terraform/downloads)
2. **Install AWS CLI** — [aws.amazon.com/cli](https://aws.amazon.com/cli/)
3. **Configure AWS credentials**:
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)
   ```

---

## Step-by-Step Usage

### Step 1 — Run Bootstrap (one time only)
Creates the S3 bucket and DynamoDB table for remote state storage.
```bash
cd terraform/bootstrap
terraform init
terraform apply
```

### Step 2 — Fill in your values
Edit `terraform/terraform.tfvars`:
```hcl
key_name             = "your-key-pair-name"    # from AWS Console → EC2 → Key Pairs
ssh_allowed_cidr     = "YOUR_IP/32"            # your IP address for SSH security
state_bucket_name    = "cart-api-state-12345"  # globally unique bucket name
```

### Step 3 — Enable the S3 backend
In `terraform/backend.tf`, uncomment the `terraform { backend "s3" ... }` block,
then fill in your bucket name.

### Step 4 — Initialize Terraform
```bash
cd terraform
terraform init
```

### Step 5 — Preview changes (dry run)
```bash
terraform plan -var="key_name=your-key-pair-name"
```
This shows EXACTLY what will be created/changed/deleted. Nothing happens yet.

### Step 6 — Apply (create the infrastructure)
```bash
terraform apply -var="key_name=your-key-pair-name"
```
Type `yes` when prompted. After it finishes, you'll see:

```
ec2_public_ip    = "54.123.45.67"
ec2_instance_id  = "i-0abc123def456789"
ssh_command      = "ssh -i ~/.ssh/your-key.pem ec2-user@54.123.45.67"
swagger_ui_url   = "http://54.123.45.67/docs"
```

### Step 7 — Copy EC2_HOST to GitHub Secrets
Go to: GitHub → your repo → Settings → Secrets and Variables → Actions
Add secret: `EC2_HOST` = the `ec2_public_ip` value from above.

---

## Importing Existing Resources

If you already have an EC2 instance running (deployed manually), import it
into Terraform state instead of creating a new one:

```bash
# Replace i-0abc123def456789 with your actual EC2 instance ID
terraform import aws_instance.cart_api i-0abc123def456789

# Replace sg-0abc123 with your actual security group ID
terraform import aws_security_group.cart_api_sg sg-0abc123

# Replace eipalloc-0abc123 with your Elastic IP allocation ID
terraform import aws_eip.cart_api_eip eipalloc-0abc123
```

After importing, run `terraform plan` — if it shows no changes, you're good.

---

## Destroy Everything

```bash
terraform destroy
```
This deletes ALL resources Terraform manages. Use with caution.

---

## File Structure

```
terraform/
├── versions.tf       # Terraform and provider version requirements
├── variables.tf      # All input variables with descriptions
├── main.tf           # Core resources: VPC, SG, IAM, EC2, EIP
├── outputs.tf        # Values printed after apply (IP, IDs, URLs)
├── backend.tf        # Remote state config (S3 + DynamoDB)
├── terraform.tfvars  # Your actual values (NOT committed to Git)
├── .gitignore        # Excludes state files and secrets
├── README.md         # This file
└── bootstrap/
    └── main.tf       # Creates S3 + DynamoDB for remote state (run once)
```
