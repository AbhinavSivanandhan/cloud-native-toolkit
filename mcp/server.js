import { getCostSummary } from './tools/get_cost_summary.js';
import { getInfraRisks } from './tools/get_infra_risks.js';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const loadPrompts = async () => {
  const content = await fs.readFile(path.join(__dirname, 'prompts', 'governance.md'), 'utf-8');
  return [
    {
      id: 'governance_guide',
      type: 'prompt',
      title: 'Governance Guide',
      content
    }
  ];
};

export const loadTools = () => {
  return [
    {
      id: 'get_cost_summary',
      title: 'Get Cloud Cost Summary',
      description: 'Summarizes AWS cost using Perplexity Sonar',
      run: getCostSummary
    },
    {
      id: 'get_infra_risks',
      title: 'Detect Infra Risks',
      description: 'Analyzes AWS infra for risks using Sonar',
      run: getInfraRisks
    }
  ];
};
