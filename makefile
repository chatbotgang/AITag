build:
	docker build -t asia-east1-docker.pkg.dev/cresclab-warehouse/aitag/aitag . --platform=linux/amd64
push:
	docker push asia-east1-docker.pkg.dev/cresclab-warehouse/aitag/aitag
all:
	build
	push