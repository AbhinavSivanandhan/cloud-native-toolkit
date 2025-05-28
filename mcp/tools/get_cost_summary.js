import { ask_sonar } from '../../ai/sonar_client.js';

export const getCostSummary = async (input) => {
  const json = typeof input === 'string' ? input : JSON.stringify(input);
  const prompt = `Analyze the following AWS cost data and suggest areas for optimization:\n\n${json}`;
  const response = await ask_sonar(prompt);
  return { result: response };
};
