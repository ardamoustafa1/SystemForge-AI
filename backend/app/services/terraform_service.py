"""
Generate a downloadable Terraform IaC ZIP from a design's AI output.

Builds a base AWS stack based on detected components.
"""

import io
import re
import zipfile
from textwrap import dedent

from app.schemas.design import DesignInputPayload, DesignOutputPayload


def _detect(stack: str, keywords: list[str]) -> bool:
    low = stack.lower()
    return any(kw in low for kw in keywords)


def _readme(title: str) -> str:
    return dedent(f"""\
        # {title} - Terraform Infrastructure setup

        > Auto-generated AWS Infrastructure as Code by **SystemForge AI**.

        ## Getting Started
        
        1. Install Terraform
        2. Configure AWS credentials (`aws configure`)
        3. Run the following commands:

        ```bash
        terraform init
        terraform plan
        terraform apply
        ```

        *Review the resources before applying to avoid unexpected AWS charges!*
    """)


def _main_tf(flags: dict[str, bool]) -> str:
    body = dedent("""\
        provider "aws" {
          region = var.aws_region
        }

        # --- Base VPC ---
        module "vpc" {
          source  = "terraform-aws-modules/vpc/aws"
          version = "5.0.0"
          
          name = "${var.project_name}-vpc"
          cidr = "10.0.0.0/16"
          
          azs             = ["${var.aws_region}a", "${var.aws_region}b"]
          private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
          public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]
          
          enable_nat_gateway = true
          single_nat_gateway = true
        }

        # --- Compute (ECS Fargate via Modules) ---
        resource "aws_ecs_cluster" "app_cluster" {
          name = "${var.project_name}-cluster"
        }
    """)

    if flags.get("postgres"):
        body += dedent("""\

            # --- RDS PostgreSQL ---
            module "db" {
              source  = "terraform-aws-modules/rds/aws"
              version = "6.0.0"

              identifier = "${var.project_name}-db"
              engine     = "postgres"
              engine_version = "15"
              instance_class = "db.t4g.micro"
              allocated_storage = 20

              db_name  = "appdb"
              username = "postgres"
              port     = 5432

              vpc_security_group_ids = [module.vpc.default_security_group_id]
              subnet_ids             = module.vpc.private_subnets
              
              skip_final_snapshot = true
            }
        """)

    if flags.get("redis"):
        body += dedent("""\

            # --- ElastiCache Redis ---
            resource "aws_elasticache_cluster" "redis" {
              cluster_id           = "${var.project_name}-redis"
              engine               = "redis"
              node_type            = "cache.t4g.micro"
              num_cache_nodes      = 1
              parameter_group_name = "default.redis7"
              port                 = 6379
              security_group_ids   = [module.vpc.default_security_group_id]
              subnet_group_name    = aws_elasticache_subnet_group.redis_subnet.name
            }

            resource "aws_elasticache_subnet_group" "redis_subnet" {
              name       = "${var.project_name}-redis-subnet"
              subnet_ids = module.vpc.private_subnets
            }
        """)

    if flags.get("mongo"):
        body += dedent("""\

            # --- DocumentDB (MongoDB Compatible) ---
            resource "aws_docdb_cluster" "mongo" {
              cluster_identifier      = "${var.project_name}-docdb"
              engine                  = "docdb"
              master_username         = "admin"
              master_password         = "changeme123"
              skip_final_snapshot     = true
              vpc_security_group_ids  = [module.vpc.default_security_group_id]
              db_subnet_group_name    = aws_docdb_subnet_group.mongo_subnet.name
            }

            resource "aws_docdb_cluster_instance" "mongo_instance" {
              count              = 1
              identifier         = "${var.project_name}-docdb-instance-${count.index}"
              cluster_identifier = aws_docdb_cluster.mongo.id
              instance_class     = "db.t3.medium"
            }
            
            resource "aws_docdb_subnet_group" "mongo_subnet" {
              name       = "${var.project_name}-mongo-subnet"
              subnet_ids = module.vpc.private_subnets
            }
        """)

    return body


def _variables_tf() -> str:
    return dedent("""\
        variable "aws_region" {
          description = "AWS Region to deploy to"
          type        = string
          default     = "us-east-1"
        }

        variable "project_name" {
          description = "Name prefix for all resources"
          type        = string
          default     = "systemforge-app"
        }
    """)


def _outputs_tf(flags: dict[str, bool]) -> str:
    body = dedent("""\
        output "vpc_id" {
          value = module.vpc.vpc_id
        }
    """)
    if flags.get("postgres"):
        body += dedent("""\
            output "db_endpoint" {
              value = module.db.db_instance_endpoint
            }
        """)
    if flags.get("redis"):
        body += dedent("""\
            output "redis_endpoint" {
              value = aws_elasticache_cluster.redis.cache_nodes[0].address
            }
        """)
    return body


def build_terraform_zip(
    title: str,
    design_input: DesignInputPayload,
    design_output: DesignOutputPayload,
) -> bytes:
    """Return in-memory ZIP bytes for the Terraform IaC."""
    
    # We heuristically detect components like scaffold_service does
    stack = (design_input.preferred_stack or "") + " " + " ".join(design_output.core_components)

    flags: dict[str, bool] = {
        "postgres": _detect(stack, ["postgres", "postgresql", "pg"]),
        "redis": _detect(stack, ["redis"]),
        "mongo": _detect(stack, ["mongo", "mongodb"]),
    }

    if not any(flags.get(k) for k in ["postgres", "mongo"]):
        flags["postgres"] = True  # fallback defaults

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:48] or "project"  # type: ignore
        slug = f"{slug}-terraform"

        zf.writestr(f"{slug}/README.md", _readme(title))
        zf.writestr(f"{slug}/main.tf", _main_tf(flags))
        zf.writestr(f"{slug}/variables.tf", _variables_tf())
        zf.writestr(f"{slug}/outputs.tf", _outputs_tf(flags))

    return buf.getvalue()
