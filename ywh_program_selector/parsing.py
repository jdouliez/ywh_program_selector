"""Data parsing utilities - IP, domain, name extraction."""

import ipaddress
import re
from typing import Set
from urllib.parse import urlparse


def get_name(title: str) -> str:
    """Extract clean program name from title."""
    return (title.lower()
            .replace("private bug bounty program", "")
            .replace("bug bounty program", "")
            .replace("private bugbounty", "")
            .replace("bug bounty", "")
            .replace("private program", "")
            .strip()
            .rstrip(' -')
            .title())


def is_ip(ip_string: str) -> bool:
    """Check if string is a valid IP address."""
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def get_ips_from_subnet(subnet_string: str) -> Set[str]:
    """
    Extract IP addresses from a subnet or range notation.
    
    Supports:
        - CIDR notation: 192.168.1.0/24
        - Range notation: 192.168.1.1-10
    """
    try:
        if '-' in subnet_string:
            # Range notation: 192.168.1.1-10
            base_ip, range_end = subnet_string.rsplit('.', 1)
            start, end = range_end.split('-')
            start_num, end_num = int(start), int(end)

            if not (0 <= start_num <= 255 and 0 <= end_num <= 255):
                raise ValueError("IP range must be between 0 and 255")

            return {f"{base_ip}.{i}" for i in range(start_num, end_num + 1)}
        else:
            # CIDR notation
            network = ipaddress.ip_network(subnet_string, strict=False)
            return {str(ip) for ip in network.hosts()}

    except ValueError as e:
        print(f"Input {subnet_string} is not a valid subnet: {e}")
        return set()


def is_valid_domain(url_string: str) -> bool:
    """Validate if string is a valid domain."""
    if not url_string.startswith(('http://', 'https://')):
        url_string = 'https://' + url_string

    try:
        parsed = urlparse(url_string)
        domain = parsed.netloc
        
        if not domain:
            return False

        domain_pattern = r'^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}[:\d]*$'
        if not re.match(domain_pattern, domain, re.IGNORECASE):
            return False

        domain = domain.split(":")[0]
        parts = domain.split('.')
        
        if len(parts) < 2:
            return False

        for part in parts:
            if len(part) > 63 or len(part) == 0:
                return False
            if not all(c.isalnum() or c == '-' for c in part):
                return False
            if part.startswith('-') or part.endswith('-'):
                return False

        path = parsed.path
        if path and path != '/':
            if not all(c.isalnum() or c in '-_.~/?' for c in path):
                return False

        return True

    except Exception:
        return False
