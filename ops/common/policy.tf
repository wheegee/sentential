data "aws_iam_policy_document" "ssm" {
  statement {
    effect = "Allow"

    actions = [
      "ssm:GetParametersByPath",
      "ssm:GetParameter"
      ]

    resources = [
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.api}/*",
      "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.api}/"
      ]
  }

  statement {
      effect = "Allow"
      actions = ["kms:Decrypt"]
      resources = [data.aws_kms_key.ssm.arn]
  }
  # Uncomment to enable lambda logging to cloudwatch
  
  statement {
    effect = "Allow"
		actions = [
								"logs:CreateLogGroup",
								"logs:CreateLogStream",
								"logs:PutLogEvents"]
		resources = ["*"]
  }
}