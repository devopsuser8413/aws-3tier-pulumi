def get_user_data_public():
    """
    User data for PUBLIC EC2 instances (bastion or monitoring).
    Currently just a placeholder — you can add tools like CloudWatch Agent or
    SSM configuration here if needed.
    """
    return """#!/bin/bash
    exec > /var/log/public-setup.log 2>&1
    set -eux

    echo "==== Starting public EC2 setup ===="
    yum update -y
    echo "Public EC2 setup complete."
    """


def get_user_data_private():
    """
    User data for PRIVATE EC2 instances (application tier).
    This script installs Python3, pip, Flask, Gunicorn, SQLAlchemy,
    creates /opt/app.py, sets up app.service, and starts it automatically.
    """
    return """#!/bin/bash
    exec > /var/log/flask-setup.log 2>&1
    set -eux

    echo "==== Starting Flask app setup ===="

    # Wait for network (important for Yum)
    until ping -c1 amazon.com &>/dev/null; do
        echo "Waiting for network..."
        sleep 5
    done

    # Install Python3 and pip
    yum update -y
    yum install -y python3
    python3 -m ensurepip
    python3 -m pip install --upgrade pip

    # Install Flask and dependencies
    pip3 install flask gunicorn sqlalchemy

    # Create Flask application
    mkdir -p /opt
    cat > /opt/app.py << 'PY'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"service": "india-states-crud", "version": "v1"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PY

    # Create a systemd service for Flask
    cat > /etc/systemd/system/app.service << 'SVC'
[Unit]
Description=Flask CRUD App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/app.py
Restart=always
RestartSec=5
User=ec2-user
WorkingDirectory=/opt
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVC

    # Enable and start the Flask app
    systemctl daemon-reload
    systemctl enable app.service
    systemctl start app.service

    echo "==== Flask app setup complete ===="
    """
