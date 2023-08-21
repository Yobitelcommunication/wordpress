import os
import boto3
private_ips = os.environ['PrivateIps']
 
privateips = private_ips.split(',')
private_ips = [f'{ip}' for ip in privateips]

def display_next_ip(displayed_ips, all_ips):
    remaining_ips = [ip for ip in all_ips if ip not in displayed_ips]
    
    if remaining_ips:
        next_ip = remaining_ips[0]
        displayed_ips.append(next_ip)
        return next_ip
    else:
        return "All IPs have been displayed."

def sub_function1_():
    try:
        # Initialize AWS S3 client
        s3 = boto3.client('s3')
        bucket_name = 'bucketforstoreprivatip'
        file_key = 'displayed_ips.txt'
        
        # Read the list of displayed IPs from S3, or initialize an empty list
        try:
            response = s3.get_object(Bucket=bucket_name, Key=file_key)
            displayed_ips = response['Body'].read().decode('utf-8').splitlines()
        except Exception as e:
            displayed_ips = []

        # Call the function to get the next IP to display
        next_ip = display_next_ip(displayed_ips, private_ips)

        # Save the updated list of displayed IPs back to S3
        try:
            s3.put_object(Bucket=bucket_name, Key=file_key, Body="\n".join(displayed_ips))
        except Exception as e:
            print("Error saving to S3:", e)
            raise  # Raising the exception to handle it later
    
        return next_ip
    except Exception as e:
        print("Error in sub_function1_:", e)
        raise  # Raising the exception to handle it later

def lambda_handler(event, context):
    try:
        # Call the sub_function1_ to get the next private IP
        private_ip = sub_function1_()
        primary_ip = os.environ['PrimaryIp']
        instance_id = os.environ['InstanceId']
        database_endpoint = os.environ['DatabaseEndpoint']
        server_name = os.environ['DomainName']
        container_name = os.environ['Containername']
        nginx_conf_path = '/etc/nginx/nginx.conf'
        line_number_to_insert = 55
        new_server_block = f'''
            server {{
                listen 80;
                server_name {server_name} www.{server_name};
                location / {{
                    proxy_pass http://{private_ip}:8080;
                    proxy_bind {primary_ip};
                    proxy_set_header Host $host;
                    proxy_set_header X-Real-IP $remote_addr;
                }} 
            }}
        '''

        client = boto3.client('ssm')
        docker_command = f"docker container run -e 'WORDPRESS_DB_HOST={database_endpoint}' -e 'WORDPRESS_DB_USER=user' -e 'WORDPRESS_DB_PASSWORD=password' -e 'WORDPRESS_DB_NAME=yobitel' -e 'WORDPRESS_TABLE_PREFIX=yobitel_{container_name}' --name {container_name} -d -p {private_ip}:8080:80 wordpress:latest"
        response = client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': [docker_command]
            }
        )
        
        print("SSM Response:", response)
        
        # Modify Nginx configuration and restart Nginx
        nginx_commands = [
            f"sudo head -n {line_number_to_insert} {nginx_conf_path} | "
            f"sudo tee /etc/nginx/nginx_temp.conf > /dev/null",
            f"echo '{new_server_block}' | sudo tee -a /etc/nginx/nginx_temp.conf > /dev/null",
            f"sudo tail -n +{line_number_to_insert + 1} {nginx_conf_path} | "
            f"sudo tee -a /etc/nginx/nginx_temp.conf > /dev/null",
            f"sudo mv /etc/nginx/nginx_temp.conf {nginx_conf_path}",
            f"sudo systemctl restart nginx"
        ]
        
        nginx_response = client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': nginx_commands
            }
        )
        
        print("Nginx Response:", nginx_response)
        
        ssl_commands = [
            f"sudo certbot --nginx -d {server_name} -d www.{server_name} -m nithincloudnative@gmail.com --agree-tos --eff-email --redirect"
        ]
        
        ssl_response = client.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',
            Parameters={
                'commands': ssl_commands
            }
        )
        
        print("SSL Response:", ssl_response)  
      
        return {
            'statusCode': 200,
            'private_ip': private_ip
        }
    except Exception as e:
        print("Error in lambda_handler:", e)
        return {
            'statusCode': 500,
            'error': 'An error occurred'
        }
    
