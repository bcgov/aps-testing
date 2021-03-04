locals {
    loc = lower(replace(var.location, " ", ""))
}

resource "azurerm_resource_group" "testfarm" {
  name     = "testfarm-resources${local.loc}"
  location = var.location
}

resource "azurerm_virtual_network" "testfarm" {
  name                = "testfarm-network-${local.loc}"
  resource_group_name = azurerm_resource_group.testfarm.name
  location            = azurerm_resource_group.testfarm.location
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "internal" {
  name                 = "internal-${local.loc}"
  resource_group_name  = azurerm_resource_group.testfarm.name
  virtual_network_name = azurerm_virtual_network.testfarm.name
  address_prefixes     = ["10.0.2.0/24"]
}

resource "azurerm_linux_virtual_machine" "farm" {
  name                = "farm-${count.index}"
  count               = var.workers
  resource_group_name = azurerm_resource_group.testfarm.name
  location            = azurerm_resource_group.testfarm.location
  size                = "Standard_D2s_v3"
  admin_username      = "adminuser"
  network_interface_ids = [
    azurerm_network_interface.farm[count.index].id,
  ]

  admin_ssh_key {
    username   = "adminuser"
    public_key = file("id_rsa.pub")
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }
}

resource "azurerm_network_interface" "farm" {
  name                = "testfarm-nic-${count.index}"
  count               = var.workers
  location            = azurerm_resource_group.testfarm.location
  resource_group_name = azurerm_resource_group.testfarm.name

  ip_configuration {
    name                          = "testconfiguration1"
    subnet_id                     = azurerm_subnet.internal.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.farm_publicip[count.index].id
  }
}

resource "azurerm_public_ip" "farm_publicip" {
    name                         = "FarmPublicIp-${count.index}"
    count                        = var.workers
    location                     = azurerm_resource_group.testfarm.location
    resource_group_name          = azurerm_resource_group.testfarm.name
    allocation_method            = "Dynamic"

    tags = {
        environment = "farm"
    }
}

output "ip_addresses" {
    value = azurerm_public_ip.farm_publicip.*.ip_address
}