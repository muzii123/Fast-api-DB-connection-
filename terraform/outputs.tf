# ── Outputs ───────────────────────────────────────────────────────────────────
# These values are printed after "terraform apply" completes.
# Copy ec2_public_ip into your GitHub Actions secret EC2_HOST.

output "ec2_public_ip" {
  description = "Static public IP of the EC2 instance (Elastic IP). Use this as EC2_HOST in GitHub Secrets."
  value       = aws_eip.cart_api_eip.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance resource ID (e.g. i-0abc123def456)"
  value       = aws_instance.cart_api.id
}

output "security_group_id" {
  description = "ID of the security group attached to the EC2 instance"
  value       = aws_security_group.cart_api_sg.id
}

output "ssh_command" {
  description = "Ready-to-use SSH command to connect to your EC2 instance"
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ec2-user@${aws_eip.cart_api_eip.public_ip}"
}

output "swagger_ui_url" {
  description = "URL to access your FastAPI Swagger UI"
  value       = "http://${aws_eip.cart_api_eip.public_ip}/docs"
}
