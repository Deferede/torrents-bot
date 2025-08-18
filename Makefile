.PHONY: env up

env:
	cp .env.example .env

up:
	docker-compose up -d torrents-bot
