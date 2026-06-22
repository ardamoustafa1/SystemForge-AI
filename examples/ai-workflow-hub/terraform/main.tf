terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

variable "name" {
  type    = string
  default = "ai-workflow-hub"
}

resource "aws_sqs_queue" "dead_letter" {
  name                      = "${var.name}-dlq"
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "workflow" {
  name                       = "${var.name}-workflow"
  visibility_timeout_seconds = 180
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 5
  })
}

output "workflow_queue_url" {
  value = aws_sqs_queue.workflow.url
}
