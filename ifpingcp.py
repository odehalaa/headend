import subprocess
import paramiko
import csv
import time
import logging

logging.basicConfig(level=logging.INFO)

def discover_devices(network):
    try:
        result = subprocess.run(['fping', '-a', '-g', network], stdout=subprocess.PIPE)
        return result.stdout.decode().splitlines()
    except Exception as e:
        logging.error(f"Error during device discovery: {e}")
        return []

def ssh_connect(ip, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, username=username, password=password, timeout=10)
        
        # Execute a command to reboot the device
        stdin, stdout, stderr = client.exec_command(' reboot', get_pty=True)
        
        # Send the password if prompted for sudo password
        stdin.write(password + '\n')
        stdin.flush()
        
        # Wait for the command to complete
        stdout.channel.recv_exit_status()
        
        # Check if there's any error reported
        stderr_str = stderr.read().decode().strip()
        if stderr_str:
            client.close()
            return f"Failed: Error executing reboot command - {stderr_str}"
        
        client.close()
        return "Success: Reboot command executed"
            
    except paramiko.SSHException as ssh_err:
        return f"Failed: SSH error - {ssh_err}"
    except Exception as e:
        return f"Failed: {e}"

if __name__ == "__main__":
    network = '192.168.1.0/24'
    username = 'root'
    password = 'root'
    csv_file = 'device_status.csv'

    print(f"Discovering devices on {network}...")
    devices = discover_devices(network)
    print(f"Discovered devices: {devices}")

    # Open CSV file for writing
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['IP Address', 'Ping Status', 'SSH Status'])

        for ip in devices:
            print(f"Attempting to SSH into {ip}...")
            ssh_status = ssh_connect(ip, username, password)
            print(f"{ip} - SSH Status: {ssh_status}")

            # Write status to CSV
            writer.writerow([ip, 'Pingable', ssh_status])
            time.sleep(1)  # To avoid too many connections at once

    print(f"Results saved to {csv_file}")
