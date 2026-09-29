# LEMP Guestbook on CSC Rahti

## 1. Project description

This project converts a three-tier Docker Compose application into a Kubernetes/OpenShift deployment on CSC Rahti.

The application consists of:

- Frontend: Nginx
- Backend: Flask/Gunicorn REST API
- Database: MySQL 8.4

Only the frontend is publicly accessible. The backend and database use internal ClusterIP Services.

Redis was later added as an internal caching layer for the backend as part of Week 5.

## 2. Architecture

```text
Internet
   |
   v
OpenShift Route
   |
   v
Frontend Service :80
   |
   v
Nginx Frontend :8080
   |
   | /api/*
   v
Backend Service :8000
   |
   v
Flask/Gunicorn Backend
   |
   v
DB Service :3306
   |
   v
MySQL 8.4
   |
   v
mysql-data PVC
```

The frontend is the only component exposed through an OpenShift Route. The backend and database are reachable only through internal Kubernetes Services.

For Week 5, Redis was added to the backend architecture:

```text
Internet
   |
   v
OpenShift Route
   |
   v
Frontend Service :80
   |
   v
Nginx Frontend :8080
   |
   | /api/*
   v
Backend Service :8000
   |
   v
Flask/Gunicorn Backend
   | \
   |  \
   |   v
   |  Redis Service :6379
   |
   v
DB Service :3306
   |
   v
MySQL 8.4
   |
   v
mysql-data PVC
```

Redis is an internal service and is not exposed through a public OpenShift Route.

## 3. Container images

The application images are stored in Docker Hub:

Backend: zainabf123/lemp-rahti-backend:1.0.0
Frontend: zainabf123/lemp-rahti-frontend:1.0.3
Database: official mysql:8.4 image
Redis: redis:7-alpine

The frontend image was updated from earlier versions during the deployment process. Version 1.0.3 is the final deployed version.

For Week 5, the backend was updated to:
zainabf123/lemp-rahti-backend:1.1.0

The new backend image contains the Redis Python dependency and the updated caching code.

## 4. OpenShift resources

The deployment contains:

Deployments
frontend
backend
db
Services
frontend — ClusterIP
backend — ClusterIP
db — ClusterIP
Other resources
frontend Route
mysql-data PersistentVolumeClaim
app-config ConfigMap
mysql-init ConfigMap
mysql-secret Secret

For Week 5, the following Redis resources were added:

Redis Deployment
Redis Service

The Redis Service exposes port 6379 internally.

The Redis Deployment runs separately from the backend and database.

The final backend deployment is configured with one replica. It was temporarily scaled to three replicas during the scaling experiment.

## 5. Configuration

The application uses a ConfigMap for non-sensitive configuration:

DB_HOST=db
DB_NAME=appdb
DB_USER=appuser

Passwords are stored in the mysql-secret Kubernetes Secret.

ConfigMaps are appropriate for ordinary configuration values that are not confidential. Secrets are used for passwords and other sensitive values.

The real Secret is not stored in Git. The repository contains only:

k8s/secret-example.yaml

with placeholder values.

Redis configuration

The backend was configured with the following environment variable:

REDIS_HOST=redis

The value redis refers to the internal Redis Service in the same Rahti project.

The Redis service uses the default Redis port:

6379

Redis does not have a public Route because it is only required by the backend.

## 6. Database initialization

The MySQL initialization script is stored in the mysql-init ConfigMap and mounted into:

/docker-entrypoint-initdb.d/init.sql

The script creates:

page_views
messages

It also inserts an initial guestbook message.

The initialization script is executed by the MySQL container when the database directory is initialized for the first time. Changing the ConfigMap does not recreate tables in an already initialized persistent database.

## 7. Persistent storage

MySQL uses the mysql-data PersistentVolumeClaim:

Storage: 1Gi
Access mode: ReadWriteOnce
Storage class: standard-csi

The PVC is mounted into the MySQL container at:

/var/lib/mysql

This keeps database data outside the lifetime of an individual MySQL Pod.

Persistence experiment

A guestbook message was added through the frontend:

My first Rahti cloud message!

The message was visible through the REST API and in MySQL.

The MySQL Pod was then deleted.

The Deployment created a replacement Pod automatically. After the replacement became ready, the previously stored message was still present.

This demonstrates that the data was stored on the PVC rather than only inside the original MySQL container.

## 8. End-to-end application test

The public application is available through the OpenShift Route:

https://frontend-cloud-services-assignment4.2.rahtiapp.fi

The frontend retrieves guestbook data through:

/api/messages

The original request path was:

Browser -> OpenShift Route -> frontend Service -> Nginx frontend Pod -> backend Service -> Flask backend Pod -> db Service -> MySQL Pod -> mysql-data PVC

After Redis was added, the backend can also use the internal Redis Service:

Browser -> OpenShift Route -> frontend Service -> Nginx frontend Pod -> backend Service -> Flask backend Pod -> Redis Service
|
v
DB Service
|
v
MySQL Pod

A successful public API request returned HTTP 200 and JSON containing the stored guestbook messages.

## 9. Database read and write

Database read

The frontend displays messages retrieved through the backend REST API.

The API endpoint:

GET /api/messages

reads data from the MySQL messages table.

After Redis was added, the backend first checks whether the message list is available in the Redis cache.

If the cached value exists, the backend returns the cached data.

If the cached value does not exist, the backend queries MySQL and stores the result in Redis.

Database write

A new message was submitted through the frontend:

My first Rahti cloud message!

The message was stored in MySQL and subsequently returned by:

GET /api/messages

This verifies the complete frontend → backend → database write path.

After Redis was added, the backend also deletes the cached messages entry after a successful database write.

This prevents the application from returning an old cached message list after a new message has been added.

## 10. Pod recovery

The backend Pod was manually deleted during the recovery experiment.

The backend Deployment automatically created a replacement Pod.

The Deployment maintains the desired number of replicas through its ReplicaSet.

The relevant relationship is:

Deployment
|
v
ReplicaSet
|
v
Backend Pod

Deleting the Pod does not delete the Deployment or ReplicaSet. The ReplicaSet creates another Pod to maintain the desired replica count.

## 11. Backend scaling

The backend Deployment was temporarily scaled from one replica to three:

backend replicas: 3

Three backend Pods were observed running simultaneously.

The backend Service continued to provide one stable internal endpoint:

backend:8000

Clients therefore communicate with the Service instead of depending on a particular backend Pod IP.

After the experiment, the backend was scaled back to one replica for the final state.

## 12. Application update

The frontend image was updated through several image versions during troubleshooting and development.

The final version is:

zainabf123/lemp-rahti-frontend:1.0.3

Version 1.0.3 visibly changed the page heading to:

Rahti Guestbook — Version 1.0.3

The OpenShift Deployment performed a rolling update. The rollout completed successfully and the final frontend Pod was running the new image.

Old ReplicaSets remain in the deployment history with zero active replicas, which provides evidence of the rollout process.

For Week 5, the backend was also updated through a new image version:

zainabf123/lemp-rahti-backend:1.1.0

This version contains the Redis dependency and the Redis caching implementation.

## 13. Problems encountered and solutions

Nginx cache-directory permission problem

The first frontend image attempted to use directories that were not writable under OpenShift's restricted container security context.

The Dockerfile was changed so the relevant Nginx directories are group-writable.

Privileged port problem

The next frontend version attempted to bind Nginx to port 80.

OpenShift's restricted container environment does not allow the container to bind to a privileged port in this setup.

Nginx was therefore changed to listen on port 8080.

The frontend Service maps:

Service port 80 -> container port 8080

The frontend then ran successfully under the restricted security context.

Missing database table

The first database initialization created page_views but not messages.

As a result, the backend returned an HTTP 500 error when requesting /api/messages.

The initialization SQL was corrected to create the messages table. The database was then recreated with a fresh PVC because MySQL initialization scripts only run when the database directory is initialized.

After recreation, both tables were present and the REST API returned HTTP 200.

Redis dependency in the backend image

During the Redis implementation, the backend initially ran an older container image that did not contain the Python Redis package.

The backend Pod returned:

ModuleNotFoundError: No module named 'redis'

The redis Python package was added to backend/requirements.txt.

A new backend image was then built and tested locally. The new image contained Redis version 8.1.0.

The new image was pushed as:

zainabf123/lemp-rahti-backend:1.1.0

The backend Deployment was updated to use the new image.

After the update, the Redis package was successfully available in the running backend Pod.

## 14. Security considerations

The architecture intentionally does not expose the MySQL or backend Services through public Routes.

The database is available through the internal:

db:3306

Service.

The backend is available through the internal:

backend:8000

Service.

Sensitive passwords are stored in a Kubernetes Secret and are not committed to Git.

The repository ignores .env files and local Secret files containing real credentials.

For production use, passwords should be strong and unique and should be rotated if they have been exposed.

## 15. Docker Compose compared with Rahti/OpenShift

Docker Compose runs the application as a group of containers on a Docker host.

Compose provides:

container definitions
a local container network
service names for communication
volume configuration
environment configuration

Rahti/OpenShift provides additional orchestration features:

Deployments
ReplicaSets
Services
persistent volume claims
Routes
declarative desired state
automatic Pod replacement
horizontal scaling
rolling updates
cluster-level scheduling

The Compose architecture and Rahti architecture therefore contain the same application tiers, but Rahti provides Kubernetes/OpenShift orchestration around those containers.

## 16. Rahti compared with cPouta

Both CSC Rahti and cPouta are CSC cloud services, but they operate at different abstraction levels.

Rahti is a container platform based on OpenShift/Kubernetes. It provides Kubernetes objects such as Pods, Deployments, Services, Routes, ConfigMaps, Secrets and PersistentVolumeClaims.

cPouta is an Infrastructure-as-a-Service environment based on OpenStack. Users work with virtual machines, networks, storage volumes and other infrastructure resources.

For this application, Rahti means that the application can be deployed as Kubernetes workloads without manually managing virtual machines for each application component.

## 17. Repository structure

The important project files are:

lemp-rahti-assignment/
├── backend/
│ ├── app.py
│ ├── Dockerfile
│ └── requirements.txt
├── db/
│ └── init/
│ └── init.sql
├── frontend/
│ ├── Dockerfile
│ ├── index.html
│ └── nginx.conf
├── k8s/
│ ├── app-config.yaml
│ ├── backend-deployment.yaml
│ ├── backend-service.yaml
│ ├── db-deployment.yaml
│ ├── db-service.yaml
│ ├── frontend-deployment.yaml
│ ├── frontend-route.yaml
│ ├── frontend-service.yaml
│ ├── mysql-init.yaml
│ ├── mysql-pvc.yaml
│ └── secret-example.yaml
├── docker-compose.dev.yml
├── .gitignore
└── README.md

The real Secret file is deliberately excluded from the repository.

The Redis resource was created in the Rahti project during the Week 5 implementation.

## 18. Deployment from the repository

After logging in to Rahti and selecting the correct project:

oc apply -f .\k8s\mysql-pvc.yaml
oc apply -f .\k8s\app-config.yaml
oc apply -f .\k8s\mysql-init.yaml

Create the Secret separately using real credentials. Do not commit the real Secret:

oc create secret generic mysql-secret `  --from-literal=DB_PASSWORD="<strong-password>"`
--from-literal=MYSQL_ROOT_PASSWORD="<strong-root-password>"

Then deploy the workloads:

oc apply -f .\k8s\db-deployment.yaml
oc apply -f .\k8s\db-service.yaml
oc apply -f .\k8s\backend-deployment.yaml
oc apply -f .\k8s\backend-service.yaml
oc apply -f .\k8s\frontend-deployment.yaml
oc apply -f .\k8s\frontend-service.yaml
oc apply -f .\k8s\frontend-route.yaml

The Redis Deployment and Service were created through the Rahti interface during the Week 5 implementation.

Check the deployment:

oc get pods
oc get deployments
oc get services
oc get route
oc get pvc

The frontend Route is then used to access the application.

## 19. Final verification

Useful verification commands are:

oc get deployments
oc get pods -o wide
oc get svc
oc get route
oc get pvc
oc get rs
oc rollout history deployment/frontend
oc rollout status deployment/frontend

The final expected state is:

frontend Deployment: 1/1
backend Deployment: 1/1
db Deployment: 1/1
mysql-data PVC: Bound
frontend: public through the Route
backend: internal ClusterIP Service
db: internal ClusterIP Service

The Week 5 Redis addition also results in:

redis Deployment: 1/1
redis: internal ClusterIP Service
redis port: 6379
redis: no public Route

The backend was tested from its Pod and successfully connected to Redis.

## 20. Evidence

The deployment work produced evidence for the required experiments, including:

frontend Route and public application
successful /api/messages response
database write through the frontend
persistent data after MySQL Pod replacement
backend Pod replacement after deletion
three backend replicas during scaling
backend Service remaining stable during scaling
successful frontend rolling update
final frontend version 1.0.3
final Deployments, Services, Route and PVC
ReplicaSet and rollout history

The Week 5 Redis implementation produced additional evidence including:

Redis Deployment and Pod running
Redis Service using port 6379
Redis not exposed through a public Route
backend configured with REDIS_HOST=redis
updated backend image containing the Redis dependency
successful backend-to-Redis connection
/api/messages successfully populating the Redis cache
successful message creation after Redis integration
Redis cache invalidation after a POST request
final frontend application working with Redis enabled

The detailed command output and screenshots can be included in the assignment report alongside this README.

## 21. Week 5 — Redis caching

Redis was added to the application as a caching layer for the backend.

The main reason for adding the cache was to avoid querying the MySQL database for every repeated request for the same message data.

The cache is implemented in the backend rather than in the frontend.

Redis cache flow

For GET /api/messages, the backend first checks Redis.

GET /api/messages
|
v
Check Redis
/ \
 HIT MISS
| |
v v
Return Query MySQL
cached |
data v
Store result
in Redis
|
v
Return data

When the cache contains the messages key, the backend returns the cached data.

When the key does not exist, the backend queries MySQL and stores the result in Redis.

The Redis cache key used by the application is:

messages

Redis deployment

A separate Redis Deployment was created in the cloud-services-assignment4 project using:

redis:7-alpine

The Redis Service exposes:

6379

Redis is only accessible inside the project and does not have a public Route.

Backend configuration

The backend Deployment was configured with:

REDIS_HOST=redis

The backend therefore connects to the Redis Service using the service name redis.

The Python Redis package was added to:

backend/requirements.txt

The backend image was rebuilt and published as:

zainabf123/lemp-rahti-backend:1.1.0

Cache invalidation

The POST /api/messages endpoint invalidates the cache after a successful database write.

The flow is:

POST /api/messages
|
v
Insert into MySQL
|
v
Commit
|
v
Delete Redis "messages" key

POST /api/messages
|
v
Insert into MySQL
|
v
Commit
|
v
Delete Redis "messages" key

This means that the next GET request does not use an outdated cached message list.

Instead, it retrieves the updated data from MySQL and stores the new result in Redis.

Redis verification

The Redis connection was tested directly from the backend Pod.

The backend successfully imported the Redis Python package:

8.1.0

The backend then tested the connection to the Redis Service:

True

This confirmed that the backend Pod could communicate with the Redis Service on port 6379.

The application endpoint was also tested.

After clearing the Redis cache, a request to:

/api/messages

created the messages cache entry.

The cache was therefore populated after a cache miss.

A POST request was then tested.

The result was:

POST status: 201
Cache after POST: False

This confirmed that the new message was successfully created and that the previous Redis cache entry was deleted.

The frontend was then refreshed and continued to display the stored messages correctly.

Week 5 Git update

The Redis implementation was committed to Git with:

Commit: 68a6f59
Message: Add Redis caching to backend

The commit contained the changes to:

backend/app.py
backend/requirements.txt

The commit was pushed successfully to the main branch.

# 22. Summary

The original three-tier application was successfully converted from Docker Compose to Kubernetes/OpenShift resources on CSC Rahti.

The final architecture keeps only the frontend public while the backend and MySQL database remain internal. MySQL data is stored on a PersistentVolumeClaim, Deployments provide Pod recovery, the backend can be scaled horizontally, and the frontend can be updated through a rolling deployment.

As part of Week 5, Redis was added as an internal caching layer for the backend. The /api/messages endpoint now checks Redis before querying MySQL, while successful message creation invalidates the cached message list.

The Redis Deployment and Service were successfully deployed in Rahti, the backend was updated to use the Redis Service, and the complete cache population and invalidation flow was tested successfully.

```

```
