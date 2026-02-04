import json


def render_graph_html(graph: dict) -> str:
    graph_json = json.dumps(graph)

    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>TalkingDB Graph</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    body {{ font-family: sans-serif; }}
    svg {{ border: 1px solid #ddd; }}
  </style>
</head>
<body>
<h2>TalkingDB Semantic Graph</h2>
<svg width="900" height="600"></svg>

<script>
const data = {graph_json};

const svg = d3.select("svg");
const width = +svg.attr("width");
const height = +svg.attr("height");

const simulation = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.edges).id(d => d.id).distance(90))
  .force("charge", d3.forceManyBody().strength(-350))
  .force("center", d3.forceCenter(width / 2, height / 2));

const link = svg.append("g")
  .attr("stroke", "#aaa")
  .selectAll("line")
  .data(data.edges)
  .enter()
  .append("line");

const node = svg.append("g")
  .selectAll("circle")
  .data(data.nodes)
  .enter()
  .append("circle")
  .attr("r", 8)
  .attr("fill", d => {{
    if (d.type === "unigram") return "#2563eb";
    if (d.type === "bigram") return "#7c3aed";
    return "#64748b";
  }})
  .call(d3.drag()
    .on("start", dragstarted)
    .on("drag", dragged)
    .on("end", dragended)
  );

node.append("title").text(d => d.id);

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
</script>
</body>
</html>
"""
