# ── Provider ──────────────────────────────────────────────────────────────────
provider "aws" {
  region = var.aws_region  # eu-north-1
}

# ── Data Sources ──────────────────────────────────────────────────────────────
data "aws_vpc" "selected" {
  default = true
}

data "aws_subnets" "available" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }
}

# ── Security Group ────────────────────────────────────────────────────────────
# This is your existing security group imported from AWS.
# We match it exactly to prevent any destroy/recreate.
resource "aws_security_group" "cart_api_sg" {
  name        = "launch-wizard-1"
  description = "launch-wizard-1 created 2026-06-08T12:55:41.730Z"
  vpc_id      = data.aws_vpc.selected.id

  # Existing rules as-is in your AWS account
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  ingress {
    description = "EC2 Instance Connect - eu-north-1"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["13.48.4.200/30"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "cart-api-sg"
    Project     = var.project_name
    Environment = var.environment
  }

  lifecycle {
    # Never destroy this SG — it's attached to a running EC2 instance
    prevent_destroy = true
    ignore_changes  = [description, ingress, egress]
  }
}

# ── IAM Role for EC2 ──────────────────────────────────────────────────────────
resource "aws_iam_role" "ec2_role" {
  name = "${var.project_name}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })

  tags = {
    Name        = "${var.project_name}-ec2-role"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "ssm_read" {
  name = "${var.project_name}-ssm-read"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ]
      Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/cart-api/*"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# ── EC2 Instance ──────────────────────────────────────────────────────────────
# NOTE: This is your EXISTING instance imported into Terraform.
# Terraform manages it going forward — it will NOT be destroyed and recreated.
resource "aws_instance" "cart_api" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.cart_api_sg.id]
  subnet_id              = data.aws_subnets.available.ids[0]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_type           = "gp3"
    volume_size           = var.root_volume_size_gb
    delete_on_termination = true
    encrypted             = true
  }

  user_data = <<-EOF
    #!/bin/bash
    set -e
    yum update -y
    yum install -y docker git nginx
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ec2-user
    mkdir -p /usr/local/lib/docker/cli-plugins
    curl -SL https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-linux-x86_64 \
      -o /usr/local/lib/docker/cli-plugins/docker-compose
    chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    systemctl enable nginx
    systemctl start nginx
    cat > /etc/nginx/conf.d/fastapi.conf << 'NGINX'
    server {
        listen 80;
        server_name _;
        location / {
            proxy_pass http://127.0.0.1:8001;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    NGINX
    nginx -t && systemctl reload nginx
    echo "8001" > /home/ec2-user/active_port.txt
    chown ec2-user:ec2-user /home/ec2-user/active_port.txt
  EOF

  tags = {
    Name        = "${var.project_name}-server"
    Project     = var.project_name
    Environment = var.environment
  }

  lifecycle {
    # Prevent Terraform from destroying the existing instance
    # if user_data or AMI differences are detected after import
    ignore_changes = [
      user_data,
      ami,
      root_block_device,
      vpc_security_group_ids,
    ]
  }
}

# ── Elastic IP ────────────────────────────────────────────────────────────────
# Your instance currently uses a dynamic IP (13.61.146.93).
# This creates a STATIC IP so it never changes on restart.
resource "aws_eip" "cart_api_eip" {
  instance = aws_instance.cart_api.id
  domain   = "vpc"

  tags = {
    Name        = "${var.project_name}-eip"
    Project     = var.project_name
    Environment = var.environment
  }

  depends_on = [aws_instance.cart_api]
}
