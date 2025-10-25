# Issue Duplicate Detector Action 🤖🔍

[![GitHub Marketplace](https://img.shields.io/badge/Marketplace-Issue%20Duplicate%20Detector-blue.svg?colorA=24292e&colorB=0366d6&style=flat&longCache=true&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5L3hsaW5rIiB2aWV3Qm94PSIwIDAgNzIgNzIiIGlkPSJsb2dvIj48cGF0aCBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik0zNiAwQzE2LjExIDAgMCAxNi4xMSAwIDM2czE2LjExIDM2IDM2IDM2IDM2LTE2LjExIDM2LTM2UzU1LjkgMCAzNiAwem0xMi42MyAzOC43NGMtMS40OCAxLjQ4LTQuOTIgMS40OC02LjQgMC0xLjQ4LTEuNDgtMS40OC00LjkyIDAtNi40IDEuNDgtMS40OCA0LjkyLTEuNDggNi40IDAgMS40OSAxLjQ4IDEuNDkgNC45MiAwIDYuNHptLTIxLjgzIDEuNDhjLTEuNDggMS40OC00LjkyIDEuNDgtNi40IDAtMS40OC0xLjQ4LTEuNDgtNC45MiAwLTYuNCAtMS4xMyAxLjA4LTEuMDggMy4xNS4xMiA0LjM3IDEuMzQgMS4zMyAzLjY0IDEuMzMgNS4xMiAwIDEuMSMtMS4xLjEzLTMuMTEtMS4wMi00LjM3em0yMS44My0xLjQ4YzEuNDkgMS40OCAxLjQ5IDQuOTIgMCA2LjQtMS40OCAxLjQ4LTQuOTIgMS40OC02LjQgMC0xLjQ4LTEuNDgtMS40OC00LjkyIDAtNi40IDEuNDgtMS40OCA0LjkyLTEuNDggNi40IDB6bS0yNC4wOC02LjQxYy0xLjU5IDAtMi44OCAxLjMtMi44OCAyLjg4cyAxLjI5IDIuODggMi44OCAyLjg4IDIuODgtMS4yOSAyLjg4LTIuODhTOTIzLjczIDMyLjM0IDIyLjE1IDMyLjM0eiIgZmlsbD0iIzAzNjZkNiIvPjwvc3ZnPg==)](https://github.com/marketplace/actions/issue-duplicate-detector) 

🤖 A smart bot to keep your issues clean. This action uses NLP to find duplicate issues, helping maintainers reduce noise and triage faster.

This GitHub Action uses Artificial Intelligence (Natural Language Processing) to analyze newly opened issues in your repository and detect potential duplicates compared to existing issues. If a high similarity is found, it posts a comment and adds a label.

**Main Features:**

* **Semantic Detection:** Compares the *meaning* of issues, not just keywords.
* **Vectorization:** Uses `sentence-transformers` (model `all-MiniLM-L6-v2`) to turn text into vectors.
* **Cosine Similarity:** Calculates the similarity score between the new issue and existing open issues.
* **Automatic Action:** Posts a comment mentioning the potential duplicate and adds a configurable label.

---

## Configuration (`inputs`)

Here are the parameters you can configure:

| Input             | Description                                                                                                                                      | Required | Default               |
| :---------------- | :----------------------------------------------------------------------------------------------------------------------------------------------- | :------- | :-------------------- |
| `github-token`    | The `GITHUB_TOKEN` provided by GitHub Actions. Needed to interact with the GitHub API (post comments, add labels).                                | `true`   | -                     |
| `threshold`       | The minimum similarity score (between `0.0` and `1.0`) to consider an issue a potential duplicate. A higher score is stricter.                 | `false`  | `'0.95'`              |
| `duplicate-label` | The exact name of the label to add to issues identified as potential duplicates. **This label must exist in your repository.** | `false`  | `'potential-duplicate'` |

---

## Usage Example

To use this action, create a workflow file in your repository, for example `.github/workflows/check-duplicates.yml`:

```yaml
name: 'Duplicate Issue Detector (NLP)'

# Triggers when a new issue is opened
on:
  issues:
    types: [opened]

jobs:
  check_duplicates:
    runs-on: ubuntu-latest

    # Permissions needed to post comments and add labels
    permissions:
      issues: write
      pull-requests: write # Although we don't touch PRs, this permission might be needed for labels in some contexts. 'issues: write' should suffice but this is safer.

    steps:
      - name: Run Duplicate Issue Detector
        # Replace YOUR-USERNAME with your GitHub username
        # Use @v1 (or the version you released)
        uses: YOUR-USERNAME/issue-duplicate-detector@v1
        with:
          # Pass the secret token provided by GitHub
          github-token: ${{ secrets.GITHUB_TOKEN }}

          # Optional: Adjust the threshold if 95% is too strict or not enough
          # threshold: '0.90'

          # Optional: Change the label name if you prefer another one
          # duplicate-label: 'possible-duplicate'