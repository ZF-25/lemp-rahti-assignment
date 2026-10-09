resource "openstack_compute_instance_v2" "web" {
  name        = var.instance_name
  image_name  = var.image_name
  flavor_name = var.flavor_name
  key_pair    = var.key_pair_name

  security_groups = [
    var.security_group_name
  ]

  user_data = file("${path.module}/cloud-init.yaml")

  network {
    name = var.network_name
  }

  lifecycle {
    ignore_changes = [user_data]
  }
}
