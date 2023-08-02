**Commands to install wordpress and configure nginx**

#Install Nginx

$sudo su

$yum update

$sudo amazon-linux-extras install nginx1

$systemctl start nginx


#Need to create secondary ip for instance and attach it

$sudo ip addr add 172.31.28.197/20 dev eth0


#Install Docker

$yum install docker

$systemctl start docker

$docker pull wordpress:latest

$docker container run --name wp -d -p 172.31.28.197:8080:80 2b5691e73f15 (or) docker container run --name wp -d -p 172.31.28.197:8080:80 wordpress:latest


#Configure Nginx file

$vi /etc/nginx/nginx.conf

#Add this below configuration in that file

$Server block for site1 on port 80

    server {
        listen 80;                                             
        server_name sitename;

        location / {
            proxy_pass http://172.31.28.197:8080; # Forward traffic to port 8080
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }

$systemctl restart nginx

