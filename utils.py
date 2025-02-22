from packaging import version
import ipaddress

def check_version(current_version: str, version_rule: str) -> bool:
    """检查版本是否满足规则"""
    try:
        if '-' in version_rule:
            # 范围检查: "1.0.0-2.0.0"
            min_ver, max_ver = version_rule.split('-')
            return (version.parse(min_ver) <= version.parse(current_version) <= 
                   version.parse(max_ver))
        
        if version_rule.startswith('>='):
            # 大于等于: ">=1.0.0"
            rule_ver = version_rule[2:]
            return version.parse(current_version) >= version.parse(rule_ver)
            
        if version_rule.startswith('<='):
            # 小于等于: "<=1.0.0"
            rule_ver = version_rule[2:]
            return version.parse(current_version) <= version.parse(rule_ver)
            
        # 精确匹配
        return version.parse(current_version) == version.parse(version_rule)
        
    except Exception:
        return False

def ip_to_int(ip: str) -> int:
    """将IP地址转换为整数"""
    try:
        ip_parts = ip.split('.')
        if len(ip_parts) != 4:
            return -1
        return sum(int(part) << (24 - 8 * i) for i, part in enumerate(ip_parts))
    except Exception:
        return -1

def check_ip(client_ip: str, ip_rule: str) -> bool:
    """检查IP是否满足规则"""
    try:
        # 分割多个规则
        rules = [r.strip() for r in ip_rule.split(',')]
        client_ip_obj = ipaddress.ip_address(client_ip)
        client_ip_int = ip_to_int(client_ip)

        for rule in rules:
            try:
                if '-' in rule:
                    # IP范围匹配: "192.168.1.1-192.168.1.100"
                    start_ip, end_ip = rule.split('-')
                    start_ip_int = ip_to_int(start_ip.strip())
                    end_ip_int = ip_to_int(end_ip.strip())
                    if start_ip_int <= client_ip_int <= end_ip_int:
                        return True
                elif '*' in rule:
                    # 通配符匹配: "192.168.1.*"
                    pattern = rule.replace('*', '0/24')
                    network = ipaddress.ip_network(pattern, strict=False)
                    if client_ip_obj in network:
                        return True
                elif '/' in rule:
                    # CIDR匹配: "192.168.1.0/24"
                    network = ipaddress.ip_network(rule, strict=False)
                    if client_ip_obj in network:
                        return True
                else:
                    # 精确匹配: "192.168.1.100"
                    if client_ip == rule:
                        return True
            except Exception:
                continue

        return False
    except Exception:
        return False
