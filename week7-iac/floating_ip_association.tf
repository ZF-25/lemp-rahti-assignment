resource "openstack_networking_floatingip_associate_v2" "web" {
  floating_ip = openstack_networking_floatingip_v2.web.address
  port_id     = "0b9e6fa3-2f21-4917-9396-990795a92398"
}