import random

import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv

from test_bench_service.utilities.models import BaseDataRecord, SkewedDataRecord
from utilities.main import extract_bigrams


def train_gnn(model, edge_index, base_data, skewed_data, node_to_id, epochs=250, lr=0.05):
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    criterion = torch.nn.TripletMarginLoss(margin=1.0, p=2)

    base_indices = [node_to_id[f'base_{rec.id}'] for rec in base_data]
    skewed_indices = [node_to_id[f'skewed_{rec.id}'] for rec in skewed_data]

    for epoch in range(epochs):
        optimizer.zero_grad()

        embeddings = model(edge_index)

        anchors = embeddings[base_indices]
        positives = embeddings[skewed_indices]

        num_records = len(base_data)
        negative_indices = []
        for i in range(num_records):
            j = random.choice([x for x in range(num_records) if x != i])
            negative_indices.append(skewed_indices[j])

        negatives = embeddings[negative_indices]

        loss = criterion(anchors, positives, negatives)

        loss.backward()
        optimizer.step()

        if epoch % 20 == 0:
            print(f"Epoch: {epoch}, Loss: {loss.item()}")

    return model


def get_node_id(node_name, node_to_id):
    if node_name not in node_to_id:
        node_to_id[node_name] = len(node_to_id)
    return node_to_id[node_name]


class EntityResolutionGNN(torch.nn.Module):
    def __init__(self, num_nodes, embedding_dim=64):
        super().__init__()

        self.embedding = torch.nn.Embedding(num_nodes, embedding_dim)

        self.conv1 = SAGEConv(embedding_dim, embedding_dim)
        self.conv2 = SAGEConv(embedding_dim, embedding_dim)

    def forward(self, edge_index):
        x = self.embedding.weight

        x = self.conv1(x, edge_index)
        x = F.relu(x)

        x = self.conv2(x, edge_index)

        return F.normalize(x, p=2, dim=1)


def generate_graph(base_data: list[BaseDataRecord], skewed_data: list[SkewedDataRecord]):
    node_to_id = {}
    edges_src = []
    edges_dst = []

    def process_records(records, prefix):
        for record in records:
            ent_id = get_node_id(f"{prefix}_{record.id}", node_to_id)

            text_fields = []

            if record.names.first_name:
                text_fields.append(record.names.first_name)
            if record.names.last_name:
                text_fields.append(record.names.last_name)
            if record.names.full_names:
                text_fields.extend(record.names.full_names)

            if record.addresses.address_lines:
                text_fields.extend(record.addresses.address_lines)
            if record.addresses.postal_code:
                text_fields.append(record.addresses.postal_code)
            if record.addresses.country:
                text_fields.append(record.addresses.country)

            if record.phone_number:
                text_fields.append(record.phone_number)

            field_bigrams = set()
            for field in text_fields:
                if field and field.strip():
                    field_bigrams.update(extract_bigrams(field))

            for bg in field_bigrams:
                attr_id = get_node_id(f'bg_{bg}', node_to_id)
                edges_src.extend([ent_id, attr_id])
                edges_dst.extend([attr_id, ent_id])

    process_records(base_data, "base")
    process_records(skewed_data, "skewed")

    edge_index = torch.tensor([edges_src, edges_dst], dtype=torch.long)
    num_nodes = len(node_to_id)

    model = EntityResolutionGNN(num_nodes=num_nodes, embedding_dim=64)

    print("Starting GNN Training...")
    model = train_gnn(model, edge_index, base_data, skewed_data, node_to_id, epochs=500, lr=0.05)

    model.eval()
    with torch.no_grad():
        node_embeddings = model(edge_index)

    base_embeddings = [node_embeddings[get_node_id(f"base_{rec.id}", node_to_id)].tolist() for rec in base_data]
    skewed_embeddings = [node_embeddings[get_node_id(f"skewed_{rec.id}", node_to_id)].tolist() for rec in skewed_data]

    return base_embeddings, skewed_embeddings