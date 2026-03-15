#!/usr/bin/env bash
set -euuo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-k8s-limits-cluster-test}"

command -v kind >/dev/null 2>&1 || {
	echo "kind not found in PATH; nothing to delete." >&2
	exit 0
}

# Check if the named kind cluster exists; if so, delete it.
if kind get clusters | grep -qx "${CLUSTER_NAME}"; then
	echo "Found kind cluster '${CLUSTER_NAME}'. Deleting..."
	if kind delete cluster --name "${CLUSTER_NAME}"; then
		echo "Kind cluster '${CLUSTER_NAME}' deleted."
		exit 0
	else
		echo "Failed to delete kind cluster '${CLUSTER_NAME}'." >&2
		exit 2
	fi
else
	echo "No kind cluster named '${CLUSTER_NAME}' found. Nothing to do."
	exit 0
fi
