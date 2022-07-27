#!/bin/bash

apt-get update
apt-get -y install nginx

cp nginx.conf /etc/nginx/nginx.conf

