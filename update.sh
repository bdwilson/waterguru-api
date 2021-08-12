docker stop waterguru-api
docker rm waterguru-api
docker rmi -f waterguru-api
./build.sh
./run.sh
docker image prune
