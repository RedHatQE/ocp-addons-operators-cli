# Building cluster-sanity container
IMAGE_BUILD_CMD = "$(shell which podman 2>/dev/null || which docker)"
IMAGE_REGISTRY ?= "quay.io"
ORG_NAME ?= "redhat_msi"
IMAGE_NAME ?= "ocp-addons-operators-cli"
IMAGE_TAG ?= "latest"

FULL_OPERATOR_IMAGE ?= "$(IMAGE_REGISTRY)/$(ORG_NAME)/$(IMAGE_NAME):$(IMAGE_TAG)"

all: build-container push-container

build-container:
	$(IMAGE_BUILD_CMD) build --no-cache -f Dockerfile -t $(FULL_OPERATOR_IMAGE) .

push-container:
	$(IMAGE_BUILD_CMD) push $(FULL_OPERATOR_IMAGE)

.PHONY: all
