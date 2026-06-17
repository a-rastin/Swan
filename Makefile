PROD := docker compose -f docker-compose.yml -f docker-compose.prod.yml

.PHONY: install up down logs restart backup ps

install:        ## fresh-server one-command install
	./install.sh

up:             ## (re)build and start prod stack
	$(PROD) up -d --build

down:           ## stop stack
	$(PROD) down

logs:           ## tail logs
	$(PROD) logs -f

restart:        ## restart all services
	$(PROD) restart

ps:             ## service status
	$(PROD) ps

backup:         ## dump postgres to backup_DATE.sql
	$(PROD) exec -T db pg_dump -U swan swan > backup_$$(date +%Y%m%d_%H%M%S).sql
