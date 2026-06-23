.PHONY: deploy deploy-conf deploy-app restart anal setup bench

SERVER_IP=54.150.95.245
SSH_USER=isucon
SSH_KEY=~/.ssh/ws-default-keypair.pem

deploy: deploy-conf deploy-app restart

deploy-conf:
	scp -i $(SSH_KEY) etc/nginx/nginx.conf $(SSH_USER)@$(SERVER_IP):/tmp/nginx.conf
	scp -i $(SSH_KEY) etc/nginx/isucon.conf $(SSH_USER)@$(SERVER_IP):/tmp/isucon.conf
	scp -i $(SSH_KEY) etc/mysql/mysqld.cnf $(SSH_USER)@$(SERVER_IP):/tmp/mysqld.cnf
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "sudo cp /tmp/nginx.conf /etc/nginx/nginx.conf && sudo cp /tmp/isucon.conf /etc/nginx/sites-available/isucon.conf && sudo cp /tmp/mysqld.cnf /etc/mysql/mysql.conf.d/mysqld.cnf"

deploy-app:
	rsync -avz -e "ssh -i $(SSH_KEY) -o StrictHostKeyChecking=no" webapp/ $(SSH_USER)@$(SERVER_IP):/home/isucon/private_isu/webapp/

restart:
	@echo "--- ログの初期化 ---"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "sudo truncate -s 0 /var/log/nginx/access.log && sudo truncate -s 0 /var/log/mysql/mysql-slow.log"
	@echo "--- サービスの再起動 ---"
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "sudo systemctl restart nginx mysql isu-python"

bench: restart
	@echo "========================================="
	@echo "  RUNNING BENCHMARKER"
	@echo "========================================="
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "/home/isucon/private_isu/benchmarker/bin/benchmarker -u /home/isucon/private_isu/benchmarker/userdata -t http://127.0.0.1"

anal:
	@echo "========================================="
	@echo "  NGINX ACCESS LOG ANAL (alp)"
	@echo "========================================="
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "sudo alp ltsv --file=/var/log/nginx/access.log --sort=sum -r -m '/image/[0-9]+,/posts/[0-9]+,/@.*'"
	@echo "========================================="
	@echo "  MYSQL SLOW QUERY ANAL (pt-query-digest)"
	@echo "========================================="
	ssh -i $(SSH_KEY) $(SSH_USER)@$(SERVER_IP) "sudo pt-query-digest /var/log/mysql/mysql-slow.log | head -n 60"
