import paramiko, io, time

def ssh_exec(host: str, port: int, username: str, private_key_pem: str, command: str, timeout: int = 900) -> str:
    key = paramiko.RSAKey.from_private_key(io.StringIO(private_key_pem))
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, port=port, username=username, pkey=key, timeout=30)
    try:
        stdin, stdout, stderr = client.exec_command(command, get_pty=True, timeout=timeout)
        out = stdout.read().decode()
        err = stderr.read().decode()
        return (out + "\n" + err).strip()
    finally:
        client.close()
