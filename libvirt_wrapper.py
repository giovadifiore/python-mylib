#!/usr/bin/env python
import libvirt
import sys

# Constants used to map indexes into the domain.info() returned by libvirt
DOMAIN_INFO_STATUS = 0
DOMAIN_INFO_MAXMEM = 1
DOMAIN_INFO_MEM = 2
DOMAIN_INFO_NVCPU = 3
DOMAIN_INFO_CPU = 4


class LibvirtWrapper:
    def __init__(self):
        self.connections = dict()
        self.domains = dict()

    def connect_host(self, host, url):
        try:
            self.connections[host] = libvirt.openReadOnly(url)
        except libvirt.libvirtError:
            sys.stdout.write("Failed to establish connection to host %s with url %s" % (host, url))
            sys.stdout.flush()

    def get_info(self, host, domain):
        if host not in self.connections:
            sys.stdout.write("Host not connected. Please invoke connect_host first.")
            sys.stdout.flush()
            return

        if domain not in self.domains:
            try:
                self.domains[domain] = self.connections[host].lookupByName(domain)
            except libvirt.libvirtError:
                sys.stdout.write("Failed to get_info for host with domain %s" % domain)
                sys.stdout.flush()

        # Get info from the libvirt domain
        return self.domains[domain].info()
