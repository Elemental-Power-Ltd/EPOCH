import {OptimisationResult, Site, Task, Client} from "./State/types";

export const submitOptimisationJob = async(payload) => {
    try {
        const response = await fetch("/api/optimisation/submit-task", {
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
        const response = await fetch("/api/optimisation/queue-status", {
            method: "POST"
        });

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

export const listClients = async(): Promise<Client[]> => {
    try {
        const response = await fetch("/api/data/list-clients", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
        });

        if(!response.ok) {
            console.error(`HTTP error! Status: ${response.status}`);
            return [];
        }

        return await response.json();

    } catch (error) {
        console.error("Failed to list clients", error);
        return [];
    }
}

export const listSites = async(client_id: string): Promise<Site[]> => {
    const payload = {client_id: client_id};

    try {
        const response = await fetch("/api/data/list-sites", {
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
        const response = await fetch("/api/data/list-optimisation-tasks", {
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
        const response = await fetch("/api/data/get-optimisation-results", {
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

export const generateAllData = async (site_id: string, start_ts: string, end_ts: string) => {
    const payload = { site_id, start_ts, end_ts };
  
    try {
      const response = await fetch("/api/data/generate-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
  
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
  
      return await response.json();
    } catch (error) {
      console.error("Failed to generate data:", error);
      throw error;
    }
  }