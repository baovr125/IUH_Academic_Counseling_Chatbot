export interface ArchitectureNode {
  id: string;
  name: string;
  subTitle: string;
  category: 'client' | 'gateway' | 'service' | 'worker' | 'storage';
  x: number; // percentage (0 - 100)
  y: number; // percentage (0 - 100)
  width?: number;
  height?: number;
  iconName: string;
  color: string;
  accentBg: string;
  borderColor: string;
  details: string[];
  port?: string;
  isNewOrUpgraded?: boolean;
}

export interface DataPacketFlow {
  id: string;
  fromNodeId: string;
  toNodeId: string;
  label: string;
  color: string;
  startProgress: number; // 0 to 1
  endProgress: number;   // 0 to 1
  particleType?: 'dot' | 'packet' | 'stream';
}

export interface ImportantFile {
  path: string;
  folder: string;
  fileName: string;
  badge: string;
  badgeColor: string;
  description: string;
  keyContributions: string[];
  codeSnippet: string;
  highlightedLines?: number[];
  language?: string;
}

export interface FolderNode {
  name: string;
  path: string;
  isFolder: boolean;
  children?: FolderNode[];
  importantFileId?: string;
}
