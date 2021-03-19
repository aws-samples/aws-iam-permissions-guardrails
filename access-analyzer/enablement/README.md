# Prerequisites

Ensure that you have enabled a [delegated administrator for Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-settings.html). Instructions to add a delegated administrator can be found [here](https://docs.aws.amazon.com/IAM/latest/UserGuide/access-analyzer-settings.html).


# Enabling Account Analyzer for all accounts and regions

Create an IAM Access Analyzer with an account zone of trust in all regions, in all accounts, and all future accounts in this AWS Organization.

Run the following stack set creation from your primary billing account.

The following creates account analyzers in each of your accounts and regions in your AWS Organization.
```
python create-account-analyzer-stack-set.py
```

You might need to use the excluded regions if your billing account has enabled or hasn't allowed specific regions.
```
python3 create-account-analyzer-stack-set.py  --excluded_regions=EXCLUDED_REGIONS_HERE
```
# Enabling an Organization analyzer for all regions

The following creates an organization analyzer in your delegated account in all regions.

```
python3 create-org-analyzer-stack-set.py  --delegated=DELEGATED_ACCOUNT_NUMBER_HERE
```

 You might need to use the excluded regions if your billing account has enabled or hasn't allowed specific regions.
```
python3 create-org-analyzer-stack-set.py  --delegated=DELEGATED_ACCOUNT_NUMBER_HERE --excluded_regions=EXCLUDED_REGIONS_HERE
```
