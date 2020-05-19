---
layout: default
---



## AWS CodeCommit

| Identifier       | Guardrail                                                                   | Rationale                                                                                                                                                                                                                                                          | Remediation                                                                                                           | References   | IAM Actions                                                                                                             |
|:-----------------|:----------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------|:-------------|:------------------------------------------------------------------------------------------------------------------------|
| IAM-CODECOMMIT-1 | DeleteRepository action for CodeCommit is only allowed to whitelisted roles | CodeCommit acts as the source of truth for the versioning of different projects used by the application and/or central IT teams. If privileges to delete repository are not clearly managed, it can lead to accidental deletion of repository leading to data loss | Addingaws:ResourceTag/${TagKey}in the IAM policy’s condition to only allow whitelisted roles to delete the repository |              | [codecommit:DeleteRepository](https://docs.aws.amazon.com/codecommit/latest/APIReference/API_DeleteRepository.html)<br> |