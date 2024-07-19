import nmap


def scan_network(network_range, ports='443'):
    nm = nmap.PortScanner()
    nm.scan(hosts=network_range, arguments=f'-p {ports} --script ssl-enum-ciphers')

    report = []

    for host in nm.all_hosts():
        host_report = {
            "host": host,
            "issues": []
        }
        if nm[host].state() == 'up':
            for proto in nm[host].all_protocols():
                lport = nm[host][proto].keys()
                for port in lport:
                    if 'script' in nm[host][proto][port]:
                        if 'ssl-enum-ciphers' in nm[host][proto][port]['script']:
                            output = nm[host][proto][port]['script']['ssl-enum-ciphers']
                            if 'TLSv1.0' in output or 'TLSv1.1' in output:
                                issue = {
                                    "port": port,
                                    "output": output
                                }
                                host_report["issues"].append(issue)
        report.append(host_report)

    return report


def save_report(report, filename):
    with open(filename, 'w') as f:
        for host in report:
            f.write(f'Scanning host: {host["host"]}\n')
            if host["issues"]:
                for issue in host["issues"]:
                    f.write(f'Port : {issue["port"]}\n')
                    f.write(f'[!] Deprecated TLS version detected\n')
                    f.write(issue["output"])
                    f.write('\n')
            else:
                f.write('No deprecated TLS versions detected\n')
            f.write('\n')



global_network = '129.187.45.0/29'
intern_network = '10.162.94.0/24'

# print('Scanning Global Network...')
# global_report = scan_network(global_network)

print('Scanning Intern Network...')
intern_report = scan_network(intern_network)

print(intern_report)
# save_report(global_report, 'global_network_report.txt')
save_report(intern_report, 'intern_network_report.txt')

print('Reports saved.')
