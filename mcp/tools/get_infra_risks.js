import { ask_sonar } from '../../ai/sonar_client.js';

export const getInfraRisks = async (input) => {
  const prompt = `Review this AWS infrastructure state and identify any security or cost risks. Suggest any missing tags, open ports, or misconfigurations:\n\n${JSON.stringify(input)}`;
  const response = await ask_sonar(prompt);
  return { result: response };
};
