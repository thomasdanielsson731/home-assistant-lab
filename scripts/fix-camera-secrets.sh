#!/bin/sh
# Fix camera IPs in /config/secrets.yaml (run on HA host)
grep -v 'driveway_wide_camera_ip' /config/secrets.yaml | grep -v 'backyard_camera_ip' > /tmp/secrets_fix.yaml
cat >> /tmp/secrets_fix.yaml <<'EOF'
driveway_wide_camera_ip: "192.168.68.203"
backyard_camera_ip: "192.168.68.202"
EOF
mv /tmp/secrets_fix.yaml /config/secrets.yaml
grep _camera_ip /config/secrets.yaml
