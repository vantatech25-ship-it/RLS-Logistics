use crate::graph::{Hub, LogisticsNetwork, PathResult};
use serde::{Deserialize, Serialize};
use reqwest;
use serde_json::json;

/// GNN-inspired route scoring using hub features as a message-passing simulation.
/// When a full PyTorch/tch-rs GNN model is trained, this module will load it
/// and run inference. For now this uses a feature-weighted heuristic that
/// mirrors what a GNN aggregation step would compute.
pub struct GnnRouter;

/// Aggregated node features for GNN input (mirror of a graph embedding vector).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HubFeatures {
    pub hub_id: String,
    /// Normalised load 0–1
    pub load_factor: f64,
    /// Number of direct connections (degree centrality proxy)
    pub connectivity: usize,
    /// Computed GNN-style congestion score (lower = better to route through)
    pub congestion_score: f64,
}

#[derive(Debug, Serialize)]
struct GnnPredictRequest {
    hub_features: Vec<serde_json::Value>,
    edges: Vec<Vec<usize>>,
}

#[derive(Debug, Deserialize)]
struct GnnPredictResponse {
    scores: Vec<f64>,
}

impl GnnRouter {
    /// Scores every hub in the network. Attempts to use Python GNN sidecar,
    /// falling back to heuristic if sidecar is unreachable.
    pub async fn score_hubs(network: &LogisticsNetwork) -> Vec<HubFeatures> {
        let mut hub_list = Vec::new();
        let mut hub_indices = Vec::new();

        for (hub_id, &node_idx) in &network.hub_index {
            let hub: &Hub = &network.graph[node_idx];
            if !hub.active { continue; }
            hub_list.push((hub_id.clone(), hub, node_idx));
            hub_indices.push(node_idx);
        }

        // Prepare request for sidecar
        let mut hub_json = Vec::new();
        for (_, hub, node_idx) in &hub_list {
            let connectivity = network.graph.neighbors(*node_idx).count();
            hub_json.push(serde_json::json!({
                "load_factor": hub.load_factor,
                "connectivity": connectivity,
                "latitude": hub.latitude,
                "longitude": hub.longitude,
                "congestion_score": 0.0 // placeholder for input
            }));
        }

        let edges: Vec<Vec<usize>> = network.graph.edge_indices()
            .map(|e| {
                let (a, b) = network.graph.edge_endpoints(e).unwrap();
                // Map NodeIndex back to our local hub_list position
                let ia = hub_indices.iter().position(|&x| x == a).unwrap();
                let ib = hub_indices.iter().position(|&x| x == b).unwrap();
                vec![ia, ib]
            }).collect();

        let client = reqwest::Client::new();
        let res = client.post("http://localhost:8000/predict")
            .json(&GnnPredictRequest { hub_features: hub_json, edges })
            .send()
            .await;

        let mut features = Vec::new();

        match res {
            Ok(resp) if resp.status().is_success() => {
                if let Ok(data) = resp.json::<GnnPredictResponse>().await {
                    for (i, (hub_id, hub, node_idx)) in hub_list.into_iter().enumerate() {
                        features.push(HubFeatures {
                            hub_id,
                            load_factor: hub.load_factor,
                            connectivity: network.graph.neighbors(node_idx).count(),
                            congestion_score: data.scores[i],
                        });
                    }
                }
            }
            _ => {
                // Fallback to heuristic
                for (hub_id, hub, node_idx) in hub_list {
                    let connectivity = network.graph.neighbors(node_idx).count();
                    let congestion_score = hub.load_factor * 0.6 + (1.0 / (connectivity as f64 + 1.0)) * 0.4;
                    features.push(HubFeatures {
                        hub_id,
                        load_factor: hub.load_factor,
                        connectivity,
                        congestion_score,
                    });
                }
            }
        }

        // Sort ascending by congestion score (best hub first)
        features.sort_by(|a, b| a.congestion_score.partial_cmp(&b.congestion_score).unwrap());
        features
    }

    /// Recommends the optimal route, weighted by GNN hub scores.
    /// Applies a congestion surcharge on paths that traverse congested hubs.
    pub async fn recommend_route(
        network: &LogisticsNetwork,
        from_id: &str,
        to_id: &str,
    ) -> Option<GnnRouteRecommendation> {
        let base_path = network.shortest_path(from_id, to_id)?;
        let hub_scores = Self::score_hubs(network).await;

        // Compute a congestion surcharge: average score of from/to hubs
        let from_score = hub_scores.iter().find(|h| h.hub_id == from_id)
            .map(|h| h.congestion_score).unwrap_or(0.5);
        let to_score = hub_scores.iter().find(|h| h.hub_id == to_id)
            .map(|h| h.congestion_score).unwrap_or(0.5);

        let gnn_adjustment = ((from_score + to_score) / 2.0) as f32;
        let adjusted_cost = base_path.total_cost * (1.0 + gnn_adjustment);

        // Confidence 0–100: inverse of gnn_adjustment
        let confidence = ((1.0 - gnn_adjustment as f64) * 100.0).clamp(0.0, 100.0) as u8;

        Some(GnnRouteRecommendation {
            path: base_path,
            gnn_adjustment,
            adjusted_cost,
            confidence,
            hub_features: hub_scores,
        })
    }
}

/// The final recommendation returned by the GNN router.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GnnRouteRecommendation {
    pub path: PathResult,
    /// Fractional cost adjustment from GNN congestion model (0.0 = no adjustment)
    pub gnn_adjustment: f32,
    /// Final recommended cost after GNN scoring
    pub adjusted_cost: f32,
    /// Route confidence score 0–100
    pub confidence: u8,
    /// Full hub feature vectors for Digital Twin visualization
    pub hub_features: Vec<HubFeatures>,
}
