# LEMP Guestbook on CSC Rahti

## 1. Project description

This project converts a three-tier Docker Compose application into a Kubernetes/OpenShift deployment on CSC Rahti.

The application consists of:

- Frontend: Nginx
- Backend: Flask/Gunicorn REST API
- Database: MySQL 8.4

Only the frontend is publicly accessible. The backend and database use internal ClusterIP Services.

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
>>    |
>>    v
>> Flask/Gunicorn Backend
>>    |
>>    v
>> DB Service :3306
>>    |
>>    v
>> MySQL 8.4
>>    |
>>    v
>> mysql-data PVC
>>
The frontend is the only component exposed through an OpenShift Route. The backend and database are reachable only through internal Kubernetes Services.

## 3. Container images

The application images are stored in Docker Hub:

Backend: zainabf123/lemp-rahti-backend:1.0.0
Frontend: zainabf123/lemp-rahti-frontend:1.0.3
Database: official mysql:8.4 image

The frontend image was updated from earlier versions during the deployment process. Version 1.0.3 is the final deployed version.

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

http://frontend-cloud-services-assignment4.2.rahtiapp.fi

The frontend retrieves guestbook data through:

/api/messages

The request path is:

Browser
  -> OpenShift Route
  -> frontend Service
  -> Nginx frontend Pod
  -> backend Service
  -> Flask backend Pod
  -> db Service
  -> MySQL Pod
  -> mysql-data PVC

A successful public API request returned HTTP 200 and JSON containing the stored guestbook messages.

## 9. Database read and write
Database read

The frontend displays messages retrieved through the backend REST API.

The API endpoint:

GET /api/messages

reads data from the MySQL messages table.

Database write

A new message was submitted through the frontend:

My first Rahti cloud message!

The message was stored in MySQL and subsequently returned by:

GET /api/messages

This verifies the complete frontend → backend → database write path.

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
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── db/
│   └── init/
│       └── init.sql
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   └── nginx.conf
├── k8s/
│   ├── app-config.yaml
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── db-deployment.yaml
│   ├── db-service.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-route.yaml
│   ├── frontend-service.yaml
│   ├── mysql-init.yaml
│   ├── mysql-pvc.yaml
│   └── secret-example.yaml
├── docker-compose.dev.yml
├── .gitignore
└── README.md

The real Secret file is deliberately excluded from the repository.

## 18. Deployment from the repository

After logging in to Rahti and selecting the correct project:

oc apply -f .\k8s\mysql-pvc.yaml
oc apply -f .\k8s\app-config.yaml
oc apply -f .\k8s\mysql-init.yaml

Create the Secret separately using real credentials. Do not commit the real Secret:

oc create secret generic mysql-secret `
  --from-literal=DB_PASSWORD="<strong-password>" `
  --from-literal=MYSQL_ROOT_PASSWORD="<strong-root-password>"

Then deploy the workloads:

oc apply -f .\k8s\db-deployment.yaml
oc apply -f .\k8s\db-service.yaml
oc apply -f .\k8s\backend-deployment.yaml
oc apply -f .\k8s\backend-service.yaml
oc apply -f .\k8s\frontend-deployment.yaml
oc apply -f .\k8s\frontend-service.yaml
oc apply -f .\k8s\frontend-route.yaml

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

The detailed command output and screenshots can be included in the assignment report alongside this README.

## 21. Summary

The original three-tier application was successfully converted from Docker Compose to Kubernetes/OpenShift resources on CSC Rahti.

The final architecture keeps only the frontend public while the backend and MySQL database remain internal. MySQL data is stored on a PersistentVolumeClaim, Deployments provide Pod recovery, the backend can be scaled horizontally, and the frontend can be updated through a rolling deployment.
```
