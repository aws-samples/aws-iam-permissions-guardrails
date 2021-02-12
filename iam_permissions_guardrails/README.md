## Service control policy CDK Construct

# Install

```
pip install git+https://github.com/aws-samples/aws-iam-permissions-guardrails@9a2ffb2d02867f11775e26b27675cbfce2afed3e
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
