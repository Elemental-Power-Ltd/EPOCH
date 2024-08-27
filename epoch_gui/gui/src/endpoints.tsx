import {OptimisationResult, Site, Task} from "./State/types";

export const submitOptimisationJob = async(payload) => {
    try {
        const response = await fetch("/api/submit-optimisation-job/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to submit configuration:", error);
    }
}

export const getStatus = async() => {
    try {
        const response = await fetch("/api/get-status/");

        if(!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        data["status"] = "ONLINE"
        return data
    } catch (error) {
        console.error("Failed to get status:", error);
        return {"status": "OFFLINE"}
    }
}

export const listSites = async(client_id: string): Promise<Site[]> => {
    const payload = {client_id: client_id};

    try {
        const response = await fetch("/api/list-sites/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if(!response.ok) {
            console.error(`HTTP error! Status: ${response.status}`);
            return [];
        }

        return await response.json();

    } catch (error) {
        console.error("Failed to list sites", error);
        return [];
    }
}

export const listOptimisationTasks = async(client_id: string): Promise<Task[]> => {
    const payload = {client_id: client_id};

    try {
        const response = await fetch("/api/list-optimisation-tasks/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if(!response.ok) {
            console.error(`HTTP error! Status: ${response.status}`);
            return [];
        }

        return await response.json();

    } catch (error) {
        console.error("Failed to list sites", error);
        return [];
    }
}

export const getOptimisationResults = async(task_id: string): Promise<OptimisationResult[]> => {
    const payload = {task_id: task_id};

    try {
        const response = await fetch("/api/get-optimisation-results/", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if(!response.ok) {
            console.error(`HTTP error! Status: ${response.status}`);
            return [];
        }

        return await response.json();

    } catch (error) {
        console.error("Failed to list sites", error);
        return [];
    }
}

