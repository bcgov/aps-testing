# API Programme Services Load Testing

The following provisions a set of VMs on Azure for the purposes of using the Locust.io load testing tool.

## Prerequisites

- Azure CLI
- Terraform 0.14+

## Estimated Timeline

For reference - the timings we see when we spin up 75 VMs.

| Task              | Duration |
| ----------------- | -------- |
| terraform apply   | 30 min   |
| ssl keyscan       | 2 min    |
| install workers   | 10 min   |
| configure workers | 1 min    |
| start master      | 1 min    |
| run tests         | depends  |
| teardown          | 20 min   |

## Costs

The default Worker VM size is `Standard_D2s_v3` which is `$0.096/hour`.

Having 60 VMs works out to be about `5.76 / hour`.

## Provisioning the Load Test Farm

```
cd terraform/workspaces/loadtesting

ssh-keygen -t rsa -b 2048 -f id_rsa -N ""

-- log into Azure so that Terraform can provision stuff
az login

terraform init

terraform apply -auto-approve

-- You may need to run `terraform apply -auto-approve` twice because of the Main Public IP not getting
-- handled correctly from the terraform module and the `null_resource.configure_farm` failing
-- Re-running will destroy `null_resource.configure_farm` and re-create, finishing the rest successfully

-- sometimes need to 'terraform import'
-- terraform import azurerm_resource_group.testfarm /subscriptions/XX/resourceGroups/testfarm-resources

-- Use the Public IP of the Main VM and Password from Terraform Apply Output
export IP=""
ssh adminuser@$IP

-- on the Main VM:

-- prepare the hosts file based on the IPs outputed from Terraform Apply Output
vi hosts

-- do the ssl keyscan
./ansible/host_list.sh

-- Public IP from Terraform Apply Output
export IP=""

-- one-time install anything we want on each of the worker VMs
ansible-playbook ansible/init.pb -i hosts -f 100 --extra-vars "MASTER_HOST=$IP"

-- update the locustfile.py on all workers and start the Locust worker
ansible-playbook ansible/farm.pb -i hosts -f 100 --extra-vars "MASTER_HOST=$IP"

```

## Verify Public IPs of workers

```
ansible-playbook ansible/query.pb -i hosts --extra-vars "MASTER_HOST=$IP"
```

## Running a test

```
locust -f ansible/locustfile.py --master --web-port 8080
```

In a browser, go to http://$IP:8080

## Kill workers

```
ansible-playbook ansible/kill.pb -i hosts -f 100 --extra-vars "MASTER_HOST=$IP"
```

## Teardown

```
terraform destroy

-- You may need to cleanup the Resource Groups - just check in Azure
-- use imp.py to get the commands to delete any remaining azure resource groups
az group list > groups.json
python3 imp.py
```

> NOTE: In Azure Console, make sure all resources are removed and Resource Groups are deleted.
