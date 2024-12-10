# curl download profile
curl https://file.io/862D3he93JY3 -o profile.ovpn

openvpn3 config-import --config profile.ovpn --name CloudConnexa --persistent

openvpn3 config-acl --show --lock-down true --grant root --config CloudConnexa

sudo systemctl enable --now openvpn3-session@CloudConnexa.service