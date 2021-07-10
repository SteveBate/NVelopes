# stop the application
docker-compose down

# stop the mongo cluster
cd containers/mongo
docker-compose down

# remove the network
docker network rm nvelopes-network