// File: mcp/index.js
import express from 'express';
import fetch from 'node-fetch';
import dotenv from 'dotenv';
import { loadPrompts, loadTools } from './server.js';

dotenv.config();

const app = express();
const PORT = 5005;
const SONAR_API_KEY = process.env.PERPLEXITY_API_KEY;

app.use(express.json());

// --- Traditional direct query support (like older version) ---
app.post('/query', async (req, res) => {
  const { messages } = req.body;

  if (!SONAR_API_KEY) {
    return res.status(500).json({ error: 'Missing PERPLEXITY_API_KEY' });
  }

  try {
    const response = await fetch('https://api.perplexity.ai/chat/completions', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${SONAR_API_KEY}`,
        'Content-Type': 'application/json',
        Accept: 'application/json'
      },
      body: JSON.stringify({
        model: 'sonar-pro',
        messages
      })
    });

    const data = await response.json();
    res.json(data);
  } catch (err) {
    console.error('❌ MCP /query error:', err);
    res.status(500).json({ error: err.message });
  }
});

// --- MCP Tools endpoint ---
app.get('/tools', (_, res) => {
  const tools = loadTools();
  res.json(tools.map(t => ({
    id: t.id,
    title: t.title,
    description: t.description
  })));
});

app.post('/tool/:id', async (req, res) => {
  const tools = loadTools();
  const tool = tools.find(t => t.id === req.params.id);
  if (!tool) return res.status(404).json({ error: 'Tool not found' });

  try {
    const output = await tool.run(req.body.input);
    res.json(output);
  } catch (err) {
    console.error(`❌ Tool '${tool.id}' error:`, err);
    res.status(500).json({ error: err.message });
  }
});

// --- MCP Prompts endpoint ---
app.get('/prompts', async (_, res) => {
  try {
    const prompts = await loadPrompts();
    res.json(prompts);
  } catch (err) {
    console.error('❌ Prompt loading error:', err);
    res.status(500).json({ error: err.message });
  }
});

// --- Server startup ---
app.listen(PORT, () => {
  console.log(`🚀 MCP server ready at http://localhost:${PORT}`);
});
