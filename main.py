import os
import json
import re
from typing import List
from dotenv import load_dotenv
import hashlib

from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError

import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from networkx.algorithms.community import greedy_modularity_communities

# ----------------------------
# Initialize Configuration
# ----------------------------
load_dotenv()

USE_CACHE = True  # Flag to use cached JSON to prevent excessive API tokens during testing

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")) # Using Gemini 2.5 Flash model

# ----------------------------
# Architectural Schema
# ----------------------------

class NodeEntity(BaseModel):
    id: str = Field(..., description="Unique snake_case identifier.")
    label: str = Field(..., description="Short, human-readable display label.")
    category: str = Field(default="concept", description="Semantic category of the node.")
    description: str = Field(default="", description="1-2 sentence semantic explanation of the system entity.")
    importance: int = Field(default=1, ge=1, le=5, description="Significance score from 1 (lowest) to 5 (highest).")
    source_reference: str = Field(default="", description="Exact quote or contextual citation from the text.")


class SystemEdge(BaseModel):
    source: str = Field(..., description="The ID of the originating node.")
    target: str = Field(..., description="The ID of the destination/terminating node.")
    interaction: str = Field(default='connects_to', description="Active verb describing the interaction (e.g., sends_data_to, authentication).")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence level of relationship extraction.")


class ArchitectureMap(BaseModel):
    nodes: List[NodeEntity] = Field(default_factory=list, description="List of system architectural components.")
    edges: List[SystemEdge] = Field(default_factory=list, description="List of dependency/interaction vectors between components.")


# ----------------------------
# Read System Blueprint Text
# ----------------------------

try:
    with open("sample.txt", "r", encoding="utf-8") as f:
        article = f.read()
except FileNotFoundError:
    # Creating a sample file if it doesn't exist
    sample_text = """
    Moon of Yesterday by Prayasha Nanda, blurb: 'I want you to imagine someone you love, anyone, and a chance to undo their biggest scar. Would you do it?
    You probably would.
    You'd want them to breathe a little lighter, live a little brighter, and love a little harder.
    Now what if I told you that they would never become dear to you since their pain never existed. Would you still undo the scar?'

    Lyra Novara made an undo when she slipped through the cracks of time, unaware of the series of events she'd set into progression. So many things differed, yet her biggest moments in life always collided. Burdened by a future she knows will no longer come to pass, she joins the program to research the Fourth Dimension of Time. But as reality keeps on washing over her, she realises that her obsession with the person she considered the closest didn't allow her to weigh the gravity of any other grief, since this one and only scar outweighed the rest.

    In this contemporary sci-fi story, as Lyra learns to let go in a world without a sky where feelings are deemed dangerous, it stopped being a question of would she go back, but rather, who was she without the person she'd held dear the most.
    """
    print("Warning: 'sample.txt' was not found. Creating a default sample text file.")
    with open("sample.txt", "w", encoding="utf-8") as f:
        f.write(sample_text)
    article = sample_text

MAX_INPUT_CHARS = 15000 # Adjust as required

if len(article) > MAX_INPUT_CHARS:
    print(f"Input text exceeds {MAX_INPUT_CHARS} characters.")
    exit(1)

prompt = f"""
Analyze the text and extract a semantic concept graph.

Requirements:

FOR EACH NODE:
- ID must be in snake_case format
- Label must be clear and readable
- Assign a short semantic category
- Categories should naturally emerge from the text, examples: theme, character, event, technology, emotion, idea
- Write a 1-2 sentence description
- Assign an importance rank (1-5)
- Provide a literal quote context reference

FOR EACH EDGE:
- Source and Target IDs must align precisely with existing Node IDs.
- Use a semantic active verb interaction.
- Assign confidence (0.0 to 1.0).

IMPORTANT:
- Limit semantic categories to a small reusable set.
- Prefer broad conceptual groupings over hyper-specific labels.
- Maximum 10 unique categories total.

Text:
{article}
"""
# So that if the prompt changes but the text is the same, it will still be refreshed
cache_key = article + prompt

article_hash = hashlib.md5(cache_key.encode()).hexdigest()

CACHE_FILE = f"cache/{article_hash}.json"
os.makedirs("cache", exist_ok=True)
OUTPUT_FILE = "graph.html"

# Helper to ensure clean key lookups
def clean_node_key(raw_id: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_]', '', str(raw_id).strip().lower().replace(" ", "_"))

validated_map = None
raw_data = {}

if USE_CACHE and os.path.exists(CACHE_FILE):
    print(f"[{CACHE_FILE}] Loading cached architecture graph data...")
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as cache_file:
            raw_data = json.load(cache_file)
        validated_map = ArchitectureMap.model_validate(raw_data)
    except Exception as err:
        print(f"Cache load failed: {err}. Proceeding with LLM retrieval.")

if validated_map is None:
    print("Requesting structured system extraction from Gemini...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ArchitectureMap,
                temperature=0.1,
            ),
        )
        
        print("\n=== RAW EXTRACTED LLM RESPONSE IN CACHE FILE===\n")
        # To Log response body, uncomment
        # print(response.text)

        if not response.text or not response.text.strip():
            raise RuntimeError(
                "Gemini returned an empty response.\n"
                "Possible causes:\n"
                "- Safety filtering\n"
                "- API quota exceeded\n"
                "- Network issue\n"
                "- Service interruption"
            )

        raw_data = json.loads(response.text)
        with open(CACHE_FILE, "w", encoding="utf-8") as cache_file:
            json.dump(raw_data, cache_file, indent=2)
            
        validated_map = ArchitectureMap.model_validate(raw_data)
        
    except ValidationError as ve:
        print(f"Validation Error detected: {ve}")
        print("Executing structural fallback reconstruction...")
        # Parsing fallback for nested discrepancies
        validated_map = ArchitectureMap(
            nodes=[
                NodeEntity(
                    id=str(n.get('id', '')).strip().lower().replace(" ", "_"),
                    label=str(n.get('label', 'Unnamed Component')),
                    category=n.get('category', 'component'),
                    description=n.get('description', ''),
                    importance=int(n.get('importance', 1)),
                    source_reference=n.get('source_reference', '')
                )
                for n in raw_data.get('nodes', []) if 'id' in n
            ],
            edges=[
                SystemEdge(
                    source=str(e.get('source')).strip().lower().replace(" ", "_"),
                    target=str(e.get('target')).strip().lower().replace(" ", "_"),
                    interaction=str(e.get('interaction', 'depends_on')),
                    confidence=float(e.get('confidence', 0.5))
                )
                for e in raw_data.get('edges', []) if 'source' in e and 'target' in e
            ]
        )
    except Exception as ex:
        print(f"Critical Pipeline Failure: {ex}")
        exit(1)

print(f"Initial extraction: Verified {len(validated_map.nodes)} nodes and {len(validated_map.edges)} edges.")

# ----------------------------
# Filter Weak Relationships
# ----------------------------

MIN_CONFIDENCE = 0.55

validated_map.edges = [
    edge for edge in validated_map.edges
    if edge.confidence >= MIN_CONFIDENCE
]

print(
    f"Retained {len(validated_map.nodes)} nodes and {len(validated_map.edges)} edges after filtering."
)

connected_nodes = set()

for edge in validated_map.edges:
    connected_nodes.add(clean_node_key(edge.source))
    connected_nodes.add(clean_node_key(edge.target))

validated_map.nodes = [
    node for node in validated_map.nodes
    if clean_node_key(node.id) in connected_nodes
]

# ----------------------------
# Construct System Dependency NetworkX Graph
# ----------------------------

G = nx.DiGraph()

CATEGORY_COLORS = {}

DEFAULT_COLORS = [
    
    "#00ffff",  # Electric Cyan
    "#f43f5e",  # rose
    "#f59e0b",  # amber
    "#8b5cf6",  # violet
    "#10b981",  # emerald
    "#5d9afb",  # pastel blue
    "#ec4899",  # pink
    "#06b6d4",  # cyan
    "#84cc16",  # lime
]

COMMUNITY_COLORS = [
    "#ff007f",  # hot pink
    "#14b8a6",  # teal
    "#ffaa00",  # gold
    "#7f00ff",  # neon violet
    "#00ff66",  # neon green
    "#ff3300",  # red-orange
    "#0066ff",  # blue
    "#ccff00",  # neon lime
    "#e600ff",  # hot magenta
]

def get_category_color(category: str):
    if category not in CATEGORY_COLORS:
        CATEGORY_COLORS[category] = DEFAULT_COLORS[
            len(CATEGORY_COLORS) % len(DEFAULT_COLORS)
        ]

    return CATEGORY_COLORS[category]

unique_edges = {}

for edge in validated_map.edges:
    key = (
        clean_node_key(edge.source),
        clean_node_key(edge.target),
        edge.interaction
    )

    if key not in unique_edges:
        unique_edges[key] = edge

validated_map.edges = list(unique_edges.values())

valid_node_ids = set()

for node in validated_map.nodes:
    clean_id = clean_node_key(node.id)
    valid_node_ids.add(clean_id)
    label = node.label[:32]
    
    tooltip_text = f"""
    '{node.label}'

    Category: {node.category}
    Importance: {node.importance}/5

    {node.description}

    Source:
    {node.source_reference}
    """.strip()
    
    G.add_node(
        clean_id,
        label=label,
        category=node.category,
        description=node.description,
        source_reference=node.source_reference,
        importance=node.importance,
        importance_value=node.importance,
        color=get_category_color(node.category),
        title=tooltip_text
    )

for edge in validated_map.edges:
    src_clean = clean_node_key(edge.source)
    tgt_clean = clean_node_key(edge.target)
    
    if src_clean in valid_node_ids and tgt_clean in valid_node_ids:
        edge_tooltip = f"""
        '{src_clean} ➔ {tgt_clean}'

        Semantic: {edge.interaction}

        Confidence: {edge.confidence * 100:.1f}%
        """.strip()
        G.add_edge(
            src_clean,
            tgt_clean,
            title=edge_tooltip,
            label=edge.interaction,
            width=1.5 + (edge.confidence * 4),
            smooth={"type": "dynamic"},
            color={
                "color": "#64748b",
                "highlight": "#38bdf8",
                "opacity": max(0.3, edge.confidence)
            }
        )
    else:
        print(f"Notice: Dropping unconnected architectural edge: [{src_clean}] -> [{tgt_clean}]")

centrality_scores = nx.degree_centrality(G)
if G.number_of_edges() > 0:
    communities = greedy_modularity_communities(G.to_undirected())
else:
    communities = []

community_map = {}

for idx, community in enumerate(communities):
    for node_id in community:
        community_map[node_id] = idx

community_counts = {}

for node_id, community_id in community_map.items():
    community_counts[community_id] = (
        community_counts.get(community_id, 0) + 1
    )

print("\nDetected Semantic Communities:\n")

for idx, community in enumerate(communities):
    print(f"Community {idx + 1}:")

    for node_id in community:
        print(f"  - {node_id}")

    print()

# ----------------------------
# Build PyVis Interactive Layout
# ----------------------------

net = Network(
    height="750px",
    width="100%",
    directed=True
)

node_importance_lookup = {
    clean_node_key(node.id): node.importance
    for node in validated_map.nodes
}

net.from_nx(G)

print("\nDetected Categories:\n")

for category, color in CATEGORY_COLORS.items():
    print(f"{category}: {color}")

net.set_options("""
var options = {
  "interaction": {
    "hover": true,
    "selectConnectedEdges": true,
    "multiselect": false,
    "dragNodes": true
  },
  "edges": {
    "arrows": {
      "to": {
        "enabled": true,
        "scaleFactor": 0.5
      }
    },
    "font": {
      "size": 11,
      "align": "horizontal",
      "strokeWidth": 2,
      "strokeColor": "#ffffff"
    }
  },
  "nodes": {
    "shape": "dot",
    "borderWidth": 2,
    "font": {
      "size": 13,
      "face": "monospace",
      "background": "rgba(255, 255, 255, 0.7)"
    }
  },
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -12000,
      "centralGravity": 0.1,
      "springLength": 240,
      "springConstant": 0.04,
      "damping": 0.09
    },
    "minVelocity": 0.75,
    "stabilization": {
      "enabled": true,
      "iterations": 150
    }
  }
}
""")

for node in net.nodes:
    score = centrality_scores.get(node["id"], 0)
    original_importance = node_importance_lookup.get(node["id"], 1)
    community_id = community_map.get(node["id"], -1)

    if community_id == -1:
        community_color = "#94a3b8"
    else:
        community_color = COMMUNITY_COLORS[community_id % len(COMMUNITY_COLORS)]

    node["size"] = (10 + (original_importance * 8) + (score * 50))
    node["color"] = {
        "background": node["color"],
        "border": community_color,
        "highlight": {
            "background": node["color"],
            "border": community_color
        }
    }
    node["title"] += f"\n\nCommunity Cluster: {community_id + 1}"

# Generate the raw HTML output file
net.write_html(OUTPUT_FILE)
legend_html = """
<div style='
    padding:16px;
    font-family:sans-serif;
    background:#0f172a;
    color:white;
    border-radius:12px;
    margin:12px;
'>
    <h3 style='margin-top:0;'>Categories</h3>
    <div style='display:flex;flex-wrap:wrap;gap:16px;'>
"""

for category, color in CATEGORY_COLORS.items():
    legend_html += f"""
    <div style='display:flex;align-items:center;gap:8px;'>
        <div style='
            width:14px;
            height:14px;
            background:{color};
            border-radius:50%;
            flex-shrink:0;
        '></div>

        <span style='font-size:14px;'>
            {category}
        </span>
    </div>
    """

legend_html += """
</div>
<hr style='margin:16px 0;border:1px solid #334155;'>

<details>
    <summary style='
        cursor:pointer;
        font-size:16px;
        font-weight:bold;
        margin-bottom:10px;
    '>
        Detected Semantic Communities
    </summary>
"""

for community_id, community in enumerate(communities):
    community_color = COMMUNITY_COLORS[
        community_id % len(COMMUNITY_COLORS)
    ]

    node_list = ", ".join(
        node.replace("_", " ").title()
        for node in sorted(community)
    )

    legend_html += f"""
    <div style='display:flex;align-items:flex-start;gap:8px;margin-bottom:10px;'>

        <div style='
            width:14px;
            height:14px;
            border-radius:50%;
            background:{community_color};
            flex-shrink:0;
            margin-top:3px;
        '></div>

        <div>
            <div style='font-size:14px;font-weight:bold;'>
                Community {community_id + 1}
                ({len(community)} nodes)
            </div>

            <div style='
                font-size:12px;
                color:#cbd5e1;
                margin-top:2px;
            '>
                {node_list}
            </div>
        </div>

    </div>
    """

legend_html += """
    </details>
</div>
"""

controls_html = """
<div id='controls-box' style='
    position:fixed;
    top:20px;
    right:20px;
    z-index:9999;
    background:rgba(255,253,245,0.85);
    color:#7c2d12;
    border:1px solid rgba(180,83,9,0.2);
    #color:white;
    padding:12px 16px;
    border-radius:12px;
'>
<div class="tape"></div>
    <div style='display:flex;justify-content:space-between;gap:12px;'>

        <strong>Controls :D</strong>

        <span
            onclick="document.getElementById('controls-box').remove()"
            style='cursor:pointer;'
        >
            ✕
        </span>

    </div>

    <div style='margin-top:6px;'>- Drag nodes</div>
    <div>- Zoom with mouse</div>
    <div>- Hover for details</div>
    <div>- Click to select</div>
</div>
"""

with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
    html = f.read()

html = html.replace(
    "</head>",
    """
    <link href="https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap" rel="stylesheet">

    <style>

    .tape {
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%) rotate(-4deg);

    width: 60px;
    height: 20px;

    background: rgba(255,248,220,0.7);

    border-left: 1px dashed rgba(0,0,0,0.08);
    border-right: 1px dashed rgba(0,0,0,0.08);

    box-shadow: 0 1px 4px rgba(0,0,0,0.15);
}
        #controls-box {
            font-family: 'Patrick Hand', cursive;
            font-size: 16px;
            opacity: 0.35;
            transition: opacity 0.2s ease;
        }

        #controls-box:hover {
            opacity: 1;
        }

        #mynetwork {
            background-color: #fffdf5;

            background-image:
                linear-gradient(
                    rgba(180,83,9,0.08) 1px,
                    transparent 1px
                ),
                linear-gradient(
                    90deg,
                    rgba(180,83,9,0.08) 1px,
                    transparent 1px
                );

            background-size: 28px 28px;
        }
    </style>

    </head>
    """,
    1
)

html = html.replace(
    "<body>",
    f"<body>\n{controls_html}\n{legend_html}\n", 1
)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Interactive HTML file built: [{OUTPUT_FILE}]")

# ----------------------------
# Static Layout Preview
# ----------------------------

try:
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42, k=1.2)
    node_colors = [nx.get_node_attributes(G, 'color').get(node, '#94a3b8') for node in G.nodes()]
    node_labels = nx.get_node_attributes(G, 'label')
    
    nx.draw(
        G, pos, labels=node_labels, with_labels=True,
        node_size=1800, font_size=7, font_weight='bold', font_color='#000000',
        node_color=node_colors, edge_color="#cbd5e1", arrows=True, arrowsize=14
    )
    
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=7)
    
    plt.title("Dependency Map", fontsize=14, fontweight='bold')
    # Save a static preview
    plt.savefig("static_blueprint.png", dpi=300, bbox_inches='tight')
    print("Static preview saved successfully as 'static_blueprint.png'")
    # plt.show() # Uncomment if running locally

except Exception as plot_err:
    print(f"Static plot preview skipped: {plot_err}")