data "aws_iam_policy_document" "combined" {
  source_policy_documents = [
    data.aws_iam_policy_document.ssm.json,
    data.aws_iam_policy_document.rds.json
  ]
}

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
      "logs:PutLogEvents"
    ]
		resources = ["*"]
  }
}

data "aws_iam_policy_document" "rds" {
  statement {
    effect = "Allow"
    actions = ["rds-db:connect"]
    resources = ["arn:aws:rds-db:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:dbuser:*/*"]
  }

  statement {
    effect = "Allow"
    actions = ["rds:DescribeDBInstances"]
    resources = ["arn:aws:rds:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*:*"]
  }
}
