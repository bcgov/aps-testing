resource "azurerm_resource_group" "testfarm" {
  name     = "testfarm-resources"
  location = "Canada East"
}

resource "azurerm_virtual_network" "testfarm" {
  name                = "testfarm-network"
  resource_group_name = azurerm_resource_group.testfarm.name
  location            = azurerm_resource_group.testfarm.location
  address_space       = ["10.0.0.0/16"]
}

resource "azurerm_subnet" "internal" {
  name                 = "internal"
  resource_group_name  = azurerm_resource_group.testfarm.name
  virtual_network_name = azurerm_virtual_network.testfarm.name
  address_prefixes     = ["10.0.2.0/24"]
}

resource "azurerm_network_interface" "main" {
  name                = "testfarm-nic"
  location            = azurerm_resource_group.testfarm.location
  resource_group_name = azurerm_resource_group.testfarm.name

  ip_configuration {
    name                          = "testconfiguration1"
    subnet_id                     = azurerm_subnet.internal.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.publicip.id
  }
}

resource "random_string" "password" {
  length           = 16
  special          = false
  override_special = "/@£$"
}

resource "azurerm_virtual_machine" "main" {
  name                  = "testfarm-main-vm"
  location              = azurerm_resource_group.testfarm.location
  resource_group_name   = azurerm_resource_group.testfarm.name
  network_interface_ids = [azurerm_network_interface.main.id]
  vm_size               = "Standard_D8_v4"

  # Uncomment this line to delete the OS disk automatically when deleting the VM
  delete_os_disk_on_termination = true

  # Uncomment this line to delete the data disks automatically when deleting the VM
  delete_data_disks_on_termination = true

  storage_image_reference {
    publisher = "Canonical"
    offer     = "UbuntuServer"
    sku       = "18.04-LTS"
    version   = "latest"
  }
  storage_os_disk {
    name              = "myosdisk1"
    caching           = "ReadWrite"
    create_option     = "FromImage"
    managed_disk_type = "Standard_LRS"
  }
  os_profile {
    computer_name  = "jumpbox"
    admin_username = "adminuser"
    admin_password = random_string.password.result
  }
  os_profile_linux_config {
    disable_password_authentication = false
  }
  tags = {
    environment = "jumpbox"
  }

}

resource "azurerm_public_ip" "publicip" {
    name                         = "myPublicIP"
    location                     = azurerm_resource_group.testfarm.location
    resource_group_name          = azurerm_resource_group.testfarm.name
    allocation_method            = "Dynamic"

    tags = {
        environment = "jumpbox"
    }
}

resource "azurerm_network_security_group" "main" {
    name                = "myNetworkSecurityGroup"
    location                     = azurerm_resource_group.testfarm.location
    resource_group_name          = azurerm_resource_group.testfarm.name

    security_rule {
        name                       = "SSH"
        priority                   = 1001
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "22"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }

    security_rule {
        name                       = "Web"
        priority                   = 1002
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "8080"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }

    security_rule {
        name                       = "Locust"
        priority                   = 1003
        direction                  = "Inbound"
        access                     = "Allow"
        protocol                   = "Tcp"
        source_port_range          = "*"
        destination_port_range     = "5557"
        source_address_prefix      = "*"
        destination_address_prefix = "*"
    }

    tags = {
        environment = "jumpbox"
    }
}

resource "azurerm_network_interface_security_group_association" "example" {
    network_interface_id      = azurerm_network_interface.main.id
    network_security_group_id = azurerm_network_security_group.main.id
}

output "public_ip" {
    value = azurerm_public_ip.publicip.ip_address
}

output "password" {
    value = random_string.password.result
}
