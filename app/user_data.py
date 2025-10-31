def get_user_data_public():
    return '''#!/bin/bash
    echo "Public EC2 setup complete" > /home/ec2-user/info.txt
    '''

def get_user_data_private():
    return '''#!/bin/bash
    yum install -y python3
    pip3 install flask gunicorn sqlalchemy
    cat > /opt/app.py << 'PY'
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"service": "india-states-crud", "version": "v1"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
PY

    cat > /etc/systemd/system/app.service << 'SVC'
[Unit]
Description=Flask CRUD App
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/app.py
Restart=always

[Install]
WantedBy=multi-user.target
SVC

    systemctl daemon-reload
    systemctl enable --now app.service
    '''
