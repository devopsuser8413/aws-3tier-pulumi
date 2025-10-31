import pulumi_aws as aws
from pathlib import Path

def create_ssh_keypair():
    # Path to your local public key
    public_key_path = Path.home() / ".ssh" / "pulumi-aws-key.pub"
    
    # Read the public key content
    public_key = public_key_path.read_text().strip()

    # Create AWS Key Pair using the public key
    keypair = aws.ec2.KeyPair(
        "pulumi-ssh-key",
        key_name="pulumi-aws-key",
        public_key=public_key
    )

    return keypair
