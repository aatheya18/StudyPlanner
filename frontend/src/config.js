// Central API configuration for Meticul
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

export const PALETTE = {
  pitchBlack: '#0d0d07',
  darkKhaki: '#31311a',
  oliveLeaf: '#54552d',
  dustyOlive: '#787940',
  palmLeaf: '#9b9d53',
  mutedOlive: '#aaad5b',
  goldenSand: '#bbbe64',
  vanillaCustard: '#d3d799',
  beige: '#e9ebcc',
  white: '#ffffff',
};

export const DEFAULT_COLOR_SWATCHES = [
  '#54552d', // Olive Leaf
  '#787940', // Dusty Olive
  '#9b9d53', // Palm Leaf
  '#bbbe64', // Golden Sand
  '#31311a', // Dark Khaki
  '#8c5836', // Terracotta accent
  '#3b6b6e', // Deep Teal
  '#684b77', // Soft Violet
];
