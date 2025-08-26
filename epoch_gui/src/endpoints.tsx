import {Site, OptimisationTaskListEntry, Client} from "./State/types";
import {
    EpochSiteData,
    OptimisationResultsResponse,
    ReproduceSimulationRequest,
    SimulationResult,
    SubmitOptimisationRequest,
    SubmitOptimisationResponse,
    SubmitSimulationRequest
} from "./Models/Endpoints";
import {Dayjs} from "dayjs";
import {TaskData} from "./Components/TaskDataViewer/TaskData.ts";


export const submitOptimisationJob = async(request: SubmitOptimisationRequest): Promise<ApiResponse<SubmitOptimisationResponse>> => {
    try {
        const response = await fetch("/api/optimisation/submit-portfolio-task", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            return {success: false, data: null, error};
        }

        const data: SubmitOptimisationResponse = await response.json();
        return {success: true, data};

    } catch (error) {
        console.error("Failed to submit configuration:", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
}

export const submitSimulation = async(request: SubmitSimulationRequest): Promise<ApiResponse<SimulationResult>> => {
    try {
        const response = await fetch("/api/optimisation/run-simulation", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const data: SimulationResult = await response.json();
        return {success: true, data};
    } catch (error) {
        console.error("Failed to run simulation", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
}

export const reproduceSimulation = async(request: ReproduceSimulationRequest): Promise<ApiResponse<SimulationResult>> => {
    try {
        const response = await fetch("/api/optimisation/reproduce-simulation", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const data: SimulationResult = await response.json();
        return {success: true, data};

    } catch (error) {
        console.error("Failed to reproduce simulation", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
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

export type ApiResponse<T> = {
    success: boolean;
    data: T | null;
    error?: string;
};

export const listClients = async (): Promise<ApiResponse<Client[]>> => {
    try {
        const response = await fetch("/api/data/list-clients", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const data: Client[] = await response.json();
        return {success: true, data};
    } catch (error) {
        console.error("Failed to list clients", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
};

export const listSites = async (client_id: string): Promise<ApiResponse<Site[]>> => {
    const payload = {client_id: client_id};

    try {
        const response = await fetch("/api/data/list-sites", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const data: Site[] = await response.json();
        return {success: true, data};
    } catch (error) {
        console.error("Failed to list sites", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
};


export const listOptimisationTasks = async(client_id: string): Promise<OptimisationTaskListEntry[]> => {
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

export const getOptimisationResults = async(task_id: string): Promise<ApiResponse<OptimisationResultsResponse>> => {
    const payload = {task_id: task_id};

    try {
        const response = await fetch("/api/data/get-optimisation-results", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if(!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const data: OptimisationResultsResponse = await response.json();
        return {success: true, data};

    } catch (error) {
        console.error("Failed to list sites", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
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

export const getLatestSiteData = async (site_id: string, start_ts: Dayjs, end_ts: Dayjs): Promise<ApiResponse<EpochSiteData>> => {
    const payload = {
        site_id,
        start_ts: start_ts.utc().format('YYYY-MM-DDTHH:mm:ss[Z]'),
        end_ts: end_ts.utc().format('YYYY-MM-DDTHH:mm:ss[Z]'),
    };

    try {
        const response = await fetch("/api/optimisation/get-latest-site-data", {
            method: "POST",
            headers: {"Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if(!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const data: EpochSiteData = await response.json();
        return {success: true, data};

    } catch (error) {
        console.error("Failed to fetch site data", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
}

export const getSiteBaseline = async (site_id: string): Promise<ApiResponse<TaskData>> => {
    const payload = {
        site_id: site_id
    }

    try {
        const response = await fetch("/api/data/get-site-baseline", {
            method: "POST",
            "headers": {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const baseline: TaskData = await response.json();
        return {success: true, data: baseline};
    } catch (error) {
        console.error("Failed to get site baseline", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
}
