---
layout: default
---



## Amazon GuardDuty

| Identifier                                                           | Guardrail                                                                                | Rationale                                                                                                                                                                                                                                           | Remediation                                                                              | References   | IAM Actions                         |
|:---------------------------------------------------------------------|:-----------------------------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------|:-------------|:------------------------------------|
| <a id="IAM-GUARDDUTY-1" href="#IAM-GUARDDUTY-1" >IAM-GUARDDUTY-1</a> | Ensure GuardDuty master account does not have permission to StopMonitoringMembers action | The master account should not have permissions to deregister a centralized member account unless it is done by a security admin Makes the accounts go “invisible” which can lead to malicious activities which cannot be viewed at org master level | Remove principal ARNs if they don’t meet the whitelisted role name and/or statement body |              | guardduty:StopMonitoringMembers<br> |