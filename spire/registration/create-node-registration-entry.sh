#!/bin/bash
set -euo pipefail

NAMESPACE="spire"
SERVER_POD="spire-server-0"
SPIFFE_ID="spiffe://example.org/ns/spire/sa/spire-agent"

echo "Creating SPIRE node registration entry..."

kubectl exec -n "$NAMESPACE" "$SERVER_POD" -- \
  /opt/spire/bin/spire-server entry create \
  -node \
  -spiffeID "$SPIFFE_ID" \
  -selector k8s_psat:cluster:demo-cluster \
  -selector k8s_psat:agent_ns:spire \
  -selector k8s_psat:agent_sa:spire-agent

echo "Node registration entry created."
