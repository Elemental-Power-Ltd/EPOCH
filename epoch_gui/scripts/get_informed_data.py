"""
This script downloads SimulationResults so that the ReportData can be viewed in the Informed embed.
- It calls /get-optimisation-results with a given task_id
- Then calls /reproduce-simulation for each portfolio_id/site_id pair in the highlighted results
- And writes these to disk as {task_id}/{portfolio_id}-{site_id}.json

- It calls Optimisation's /get-epoch-site-data to produce SiteData for each bundle found in the task
- and writes these to disk as {site_id}-{bundle_id}.json
"""
import json
import os
import requests
import sys

# SERVER_IP = "10.0.0.1"
SERVER_IP = "localhost:8760"


def get_opt_results(task_id):
    data = {"task_id": task_id}
    r = requests.post(f"http://{SERVER_IP}/api/data/get-optimisation-results", json=data)

    if r.status_code != 200:
        print("Failed to get task results. Is the task_id valid?")
        sys.exit()

    response = r.json()
    return response


def get_result_tuples(task_result):
    highlights = task_result["highlighted_results"]
    results = task_result["portfolio_results"]

    for highlight in highlights:
        portfolio_result = next((p_res for p_res in results if p_res["portfolio_id"] == highlight["portfolio_id"]),
                                None)

        if portfolio_result is None:
            print("Highlighted Result not found!")
            sys.exit()

        for site in portfolio_result["site_results"]:
            yield highlight["portfolio_id"], site["site_id"]


def reproduce_result(portfolio_id, site_id):
    data = {"portfolio_id": portfolio_id, "site_id": site_id}
    r = requests.post(f"http://{SERVER_IP}/api/optimisation/reproduce-simulation", json=data)

    if r.status_code != 200:
        print("Failed to fetch result for", data)
        sys.exit()

    return r.json()


def write_result(task_id, portfolio_id, site_id, result):
    task_dir = f"./results/{task_id}"
    os.makedirs(task_dir, exist_ok=True)

    filename = f"{portfolio_id}-{site_id}.json"
    filepath = os.path.join(task_dir, filename)

    print(f"Writing {filepath}")
    with open(filepath, 'w') as f:
        json.dump(result, f, indent=4)


def get_and_write_site(site_id, hint):
    bundle_id = hint["bundle_id"]

    data = {"site_id": site_id, "bundle_id": bundle_id}
    r = requests.post(f"http://{SERVER_IP}/api/optimisation/get-latest-site-data", json=data)

    if r.status_code != 200:
        print(f"Failed to get site data for {bundle_id}")
        sys.exit()

    sd = r.json()
    site_and_hint = {
        "siteData": sd,
        "hints": hint
    }

    sites_dir = "./sites"
    os.makedirs(sites_dir, exist_ok=True)

    filename = f"{site_id}-{bundle_id}.json"
    filepath = os.path.join(sites_dir, filename)

    print(f"Writing {filepath}")
    with open(filepath, 'w') as f:
        json.dump(site_and_hint, f, indent=4)


def main():
    if len(sys.argv) < 2:
        print("Error, you must provide a task_id")
        print("Usage: python get_portfolio_report_data $task_id")
        sys.exit()

    task_id = sys.argv[1]

    task_result = get_opt_results(task_id)

    for p_id, s_id in get_result_tuples(task_result):
        result = reproduce_result(p_id, s_id)
        write_result(task_id, p_id, s_id, result)

    for site_id in task_result["hints"]:
        get_and_write_site(site_id, task_result["hints"][site_id])


if __name__ == "__main__":
    main()
