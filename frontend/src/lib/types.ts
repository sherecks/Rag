export interface GraphNode {
  id: string;
  type: string;
  description: string;
  degree: number;
  size: number;
  color: string;
}

export interface GraphLink {
  source: string;
  target: string;
  description: string;
  keywords: string;
  weight: number;
}

export interface LegendGroup {
  label: string;
  color: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  legend: LegendGroup[];
  generated_at: number;
}
