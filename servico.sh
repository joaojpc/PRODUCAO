#!/bin/bash
echo "Houve um problema com o servidor, tentando reiniciá-lo  $(date +%F\ %T)"
sudo service nginx restart
sleep 10
sudo service gunicorn restart
