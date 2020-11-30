## Service control policy CDK Construct

# Install

```
pip install git+https://github.com/aws-samples/aws-iam-permissions-guardrails@59e06d0f7c26c5dd7423ebf1d74ea17dfc4829b2
```

# Example Usage

```
from iam_permissions_guardrails.constructs.service_control_policies import ScpPolicyResource, ScpAttachmentResource


        scp_policy_resource = ScpPolicyResource(
            self,
            "test-scp-policy-resource",
            trimmed_json=service_control_policy_string,
            description=description,
            name=name,
        )

        ScpAttachmentResource(
            self,
            "test-attachment",
            policy_id=scp_policy_resource.policy_id,
            account_targets=account_targets,
            organization_unit_targets=organization_unit_targets,
        )

```
