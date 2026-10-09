resource "openstack_networking_floatingip_v2" "web" {
  pool = "public"
}
