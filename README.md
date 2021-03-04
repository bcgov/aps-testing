
# API Programme Services Load Testing

## Prerequisites

* Azure CLI
* Terraform 0.14+

## Estimated Timeline

| Task              | Duration |
|-------------------|----------|
| terraform apply   | 30 min   |
| ssl keyscan       | 2 min    |
| install workers   | 10 min   |
| configure workers | 1 min    |
| start master      | 1 min    |
| run tests         | depends  |
| teardown          | 20 min   |

## Costs

We use `Standard_D2s_v3` VMs which is `$0.096/hour`.

Having 60 VMs works out to be about `5.76 / hour`.


## Provisioning the Load Test Farm

```
cd terraform/workspaces/loadtesting

ssh-keygen -t rsa -b 2048 -f id_rsa -N ""

-- log into Azure so that Terraform can provision stuff
az login

terraform init

terraform apply -auto-approve

-- sometimes need to 'terraform import'
-- terraform import azurerm_resource_group.testfarm /subscriptions/XX/resourceGroups/testfarm-resources

-- Use the Public IP of the Main VM and Password from Terraform Apply Output
export IP=""
ssh -i id_rsa adminuser@$IP

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

