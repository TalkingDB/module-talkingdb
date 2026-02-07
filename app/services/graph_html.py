import json


def render_graph_html(graph: dict) -> str:
    graph_json = json.dumps(graph)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>TalkingDB Graph</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    html, body {{
      margin: 0;
      padding: 0;
      width: 100%;
      height: 100%;
      overflow: hidden;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    #graph-container {{
      width: 100vw;
      height: 100vh;
    }}

    svg {{
      width: 100%;
      height: 100%;
      cursor: grab;
      background: #ffffff;
    }}

    svg:active {{
      cursor: grabbing;
    }}

    .tooltip {{
      position: absolute;
      padding: 6px 10px;
      background: rgba(15, 23, 42, 0.95);
      color: white;
      border-radius: 6px;
      font-size: 12px;
      pointer-events: none;
      white-space: nowrap;
      opacity: 0;
      transition: opacity 0.1s ease;
    }}

  </style>
</head>
<body>
<div class="tooltip" id="tooltip"></div>

<div id="graph-container">
  <svg></svg>
</div>

<script>
const data = {graph_json};

const svg = d3.select("svg");
const container = document.getElementById("graph-container");

let width = container.clientWidth;
let height = container.clientHeight;

// Root group for zooming
const g = svg.append("g");

// Zoom & pan
const zoom = d3.zoom()
  .scaleExtent([0.1, 5])
  .on("zoom", (event) => {{
    g.attr("transform", event.transform);
  }});

svg.call(zoom);

// Force simulation
const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.edges).id(d => d.id).distance(90))
  .force("charge", d3.forceManyBody().strength(-350))
  .force("center", d3.forceCenter(width / 2, height / 2));

// Links
const link = g.append("g")
  .attr("stroke", "#aaa")
  .attr("stroke-opacity", 0.7)
  .selectAll("line")
  .data(data.edges)
  .enter()
  .append("line")
  .attr("stroke-width", 1.2);

const indexColor = d3.scaleOrdinal()
  .domain([
    "file@root",
    "section@outline",
    "section@para",
    "unigram",
    "bigram",
    "trigram"
  ])
  .range([
    "#0f172a", // root
    "#2563eb", // section
    "#64748b", // paragraph
    "#16a34a", // unigram (green)
    "#d97706", // bigram (amber)
    "#dc2626"  // trigram (red)
  ]);


// Nodes
const node = g.append("g")
  .selectAll("circle")
  .data(data.nodes)
  .enter()
  .append("circle")
  .attr("r", 8)
  .attr("fill", d => indexColor(d.type ?? "unknown"))
  .call(
    d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended)
  );


// Tooltip
const tooltip = d3.select("#tooltip");

node
  .on("mouseenter", (event, d) => {{
    tooltip
      .style("opacity", 1)
      .html(d.label ?? d.id);
  }})
  .on("mousemove", (event) => {{
    tooltip
      .style("left", event.pageX + 12 + "px")
      .style("top", event.pageY + 12 + "px");
  }})
  .on("mouseleave", () => {{
    tooltip.style("opacity", 0);
  }});

// Tick update
simulation.on("tick", () => {{
  link
    .attr("x1", d => d.source.x)
    .attr("y1", d => d.source.y)
    .attr("x2", d => d.target.x)
    .attr("y2", d => d.target.y);

  node
    .attr("cx", d => d.x)
    .attr("cy", d => d.y);
}});

// Drag handlers
function dragstarted(event, d) {{
  if (!event.active) simulation.alphaTarget(0.3).restart();
  d.fx = d.x;
  d.fy = d.y;
}}

function dragged(event, d) {{
  d.fx = event.x;
  d.fy = event.y;
}}

function dragended(event, d) {{
  if (!event.active) simulation.alphaTarget(0);
  d.fx = null;
  d.fy = null;
}}

// Handle resize
window.addEventListener("resize", () => {{
  width = container.clientWidth;
  height = container.clientHeight;
  simulation.force("center", d3.forceCenter(width / 2, height / 2));
  simulation.alpha(0.3).restart();
}});
</script>

</body>
</html>
"""
