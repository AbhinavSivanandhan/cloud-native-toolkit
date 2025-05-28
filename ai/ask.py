# File: ai/ask.py

from ai.sonar_client import ask_sonar

# ✅ Original: Cost summary based on raw data
def ask_cost_governance_summary(cost_data: str) -> str:
    prompt = f"""Analyze the following AWS cost or resource data and identify:
    - Any spikes or anomalies
    - Untagged or potentially orphaned services
    - Suggestions for cost optimization or tagging improvements

    ```json
    {cost_data}
    ```
    Provide your answer in markdown format with clear headings.
    """
    return ask_sonar(prompt)


# ✅ Original: Freeform user queries
def ask_freeform(question: str) -> str:
    return ask_sonar(question)


# ✅ New: Highlight security issues in AWS resource configs
def ask_infra_risks(resource_snapshot: str) -> str:
    prompt = f"""Examine the following AWS infrastructure snapshot and identify:
    - Publicly exposed resources (S3, EC2, RDS, etc.)
    - Over-permissive IAM policies
    - Known misconfigurations or best practice violations

    ```json
    {resource_snapshot}
    ```
    Output your response in markdown format with sections: Risks, Examples, Recommendations.
    """
    return ask_sonar(prompt)


# ✅ New: Cost comparison across snapshots
def ask_cost_change_summary(before: str, after: str) -> str:
    prompt = f"""Compare these two AWS cost reports:

    -- BEFORE:
    ```json
    {before}
    ```

    -- AFTER:
    ```json
    {after}
    ```

    Identify key changes in services, cost spikes or drops, and tag/resource hygiene changes.
    Return a bullet-point summary in markdown format with helpful recommendations.
    """
    return ask_sonar(prompt)


# ✅ New: Budget-based infra plan for students/solo startups
def ask_startup_plan(budget_usd: int) -> str:
    prompt = f"""You're advising a student startup that has ${budget_usd} per month to spend on AWS.

    Recommend:
    - Cost-effective services to use (compute, DB, storage, etc.)
    - How to design a simple, secure, scalable infra
    - Budget breakdown by service
    - Tips to avoid waste

    Keep your answer clear and markdown-formatted.
    """
    return ask_sonar(prompt)
