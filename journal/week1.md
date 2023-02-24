# Week 1 — App Containerization


docker build ./ -t backend/cruddur:v1
docker build ./ -t backend/cruddur:v2

```docker container run --rm -p 4567:4567 -d backend/cruddur:v1```
```docker container run --rm -p 4568:4567 -d backend/cruddur:v2```