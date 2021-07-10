# create the shared network for the containers
docker network create -d bridge nvelopes-network

# bring up the mongo cluster
echo "bringing up mongo cluster containers"
cd containers/mongo
docker-compose up -d

echo "sleep 3"
sleep 3 # seconds

# move to root
cd ../..

# bring up the app containers
echo "starting the app containers"
docker-compose up -d

echo "done"
