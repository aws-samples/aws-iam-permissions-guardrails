## AWS IAM Permissions Guardrails

## Table of Contents
* [Background](#background)
* [Example Service Control Policies](#example-service-control-policies)
* [Frequently Asked Questions](#frequently-asked-questions)

## Background
The AWS IAM Permissions Guardrails help customers securely provision and monitor IAM permissions across a customer’s utilization of AWS Services. Our goal is to help AWS customers look around corners and understand the rationale and remediation for locking down specific IAM Permissions.

Also, our goal is to help AWS customers define a measurable approach to assess their AWS IAM posture. We are looking to compile the deep fine-grained IAM knowledge of global AWS experts and consultants in a scalable automated mechanism. The IAM Permissions Guardrails can be enforced in a CI/CD pipeline or evaluated via AWS Config Rules or assessment scripts.

Our focus is analyzing at the policy level rather than the effective permissions within an account. We want to encourage application teams to create secure policies starting in lower environments. Also, we want to reduce the blast radius due to accidental oversight and improve defense in depth, rather than relying on a single service control policy.

These IAM Permissions Guardrails are based on collective experiences. That said, if you know better ones, submit a pull request.

## Example Service Control Policies

[List](https://aws-samples.github.io/aws-iam-permissions-guardrails/guardrails/scp-guardrails.html) of example service control policies

## Frequently Asked Questions

Q. How were these guardrails created?

A. We’ve collected, cataloged, and curated our IAM knowledge based on working with a variety of AWS customers.

Q. Who is the audience for these IAM Permissions Guardrails?

A. Customers that desire help to look around corners and learn from the experiences of others.

Q. Do you have any code to evaluate IAM policies against the IAM Permissions Guardrails?

A.  We will be releasing over the course of the year tools that enable you to analyze your environment against the IAM Permissions Guardrails.

Q. I have ideas to improve this repository. What should I do?

A. Please create an issue or submit a pull request.


## Contributors
[Contributors](CONTRIBUTORS)

## License

This library is licensed under the Apache 2.0 License. See the LICENSE file.

