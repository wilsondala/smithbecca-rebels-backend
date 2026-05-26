# paixao_backend
Backend_paixao


# ligando o servidor 
# Ativar o serviço do servidor 
sudo systemctl daemon-reload
sudo systemctl enable paixao-backend

# Iniciar o servidor 
sudo systemctl start paixao-backend

# Ver status do servidor
sudo systemctl status paixao-backend

# Parar o servidor 
sudo systemctl stop paixao-backend

# Reiniciar o servidor
sudo systemctl restart paixao-backend

# Ver logs do servidor 
sudo journalctl -u paixao-backend -f



cd /opt/paixao-angola/backend
git status
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
sudo systemctl restart paixao-angola
sudo systemctl status paixao-angola
curl -s http://127.0.0.1:8000/api/v1/home-content