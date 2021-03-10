provider "azurerm" {
  features {}
}

module "main" {
    source = "./main-mod"
}

resource "null_resource" "configure_farm" {
  depends_on = [ module.main ]

  connection {
    type     = "ssh"
    user     = "adminuser"
    password = module.main.password
    host     = module.main.public_ip
  }

  provisioner "file" {
      source = "id_rsa"
      destination = "/home/adminuser/.ssh/id_rsa"
  }

  provisioner "file" {
      source = "id_rsa.pub"
      destination = "/home/adminuser/.ssh/id_rsa.pub"
  }

  provisioner "file" {
      source = "artifacts/install.sh"
      destination = "/home/adminuser/install.sh"
  }

  provisioner "file" {
      source = "artifacts/ansible"
      destination = "/home/adminuser/ansible"
  }

  provisioner "remote-exec" {
    inline = [
      "chmod 0600 .ssh/id_rsa",
      "chmod +x install.sh",
      "chmod +x ansible/host_list.sh",
      "./install.sh"
    ]
  }
}

locals {
    locations = [
        "Canada Central",
        "East US",
        "East US 2",
        # "East US 3",
        "West US",
        "West US 2",
        "West Central US",
        "Central US",
        "North Central US",
        "South Central US",
        # "Brazil Southeast",
        "Brazil South",
        "North Europe",
        "France Central",
        "UK West",
        "UK South",
        "West Europe"
    ]
}

module "farms" {
    source = "./farm-mod"
    for_each = toset(local.locations)
    
    workers  = var.workers_per_region
    size     = var.worker_size
    location = each.value
}

output "ip_addresses" {
  value = <<EOT
%{ for vms in module.farms }%{for ip in vms.ip_addresses}
${ip}%{ endfor }%{ endfor }
EOT
}

output "details" {
    value = <<README
ssh adminuser@${module.main.public_ip}

P: ${module.main.password}
README
}
