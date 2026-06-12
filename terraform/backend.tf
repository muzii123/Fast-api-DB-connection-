# ── Remote State Backend ──────────────────────────────────────────────────────
# State is stored in S3 (us-east-1 — where bootstrap ran)
# EC2 and all other resources are in eu-north-1

terraform {
  backend "s3" {
    bucket       = "cart-api-terraform-state"
    key          = "cart-api/prod/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
