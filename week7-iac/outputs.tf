output "instance_name" {
  description = "Name of the Week 7 virtual machine"
  value       = openstack_compute_instance_v2.web.name
}

output "private_ip" {
  description = "Private IP address of the Week 7 virtual machine"
  value       = openstack_compute_instance_v2.web.access_ip_v4
}

output "floating_ip" {
  description = "Public floating IP address of the Week 7 web server"
  value       = openstack_networking_floatingip_v2.web.address
}

output "assignment" {
  description = "Course assignment"
  value       = "CSC Cloud Services - Week 7"
}