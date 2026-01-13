import {Site, OptimisationTaskListRequest, Client, OptimisationTaskListResponse} from "./State/types";
import {
    EpochSiteData,
    BundleHint,
    ListBundlesResponse,
    OptimisationResultsResponse,
    ReproduceSimulationRequest,
    SimulationResult,
    SubmitOptimisationRequest,
    SubmitOptimisationResponse,
    SubmitSimulationRequest,
    SiteDataWithHints,
    FuelType,
    SolarLocation,
    UploadMeterFileResponse,
    PhppMetadata,
    addSiteRequest, CostModelResponse, CostModelRequest
} from "./Models/Endpoints";
import dayjs, {Dayjs} from "dayjs";
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


export const listOptimisationTasks = async(
    request: OptimisationTaskListRequest): Promise<ApiResponse<OptimisationTaskListResponse>> => {
    try {
        const response = await fetch("/api/data/list-optimisation-tasks", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(request)
        });

        if(!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error: error};
        }

        const data = await response.json();
        return {success: true, data};

    } catch (error) {
        console.error("Failed to list tasks", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
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

export const getLatestSiteData = async (site_id: string, start_ts: Dayjs, end_ts: Dayjs): Promise<ApiResponse<SiteDataWithHints>> => {
    try {
        // 1. Find the appropriate bundle
        const listBundlesResponse = await fetch("/api/data/list-dataset-bundles", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({site_id: site_id})
        })

        if(!listBundlesResponse.ok) {
            const error = `HTTP error! Status: ${listBundlesResponse.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        // 2. Filter to the appropriate bundle
        const allBundles: ListBundlesResponse[] = await listBundlesResponse.json();

        const validBundles = allBundles.filter(
            (bundle) => bundle.is_complete && !bundle.is_error
        );

        const matchingBundles = validBundles.filter(
            (bundle) => dayjs(bundle.start_ts).isSame(start_ts) && dayjs(bundle.end_ts).isSame(end_ts)
        );

        if (matchingBundles.length === 0) {
            return {success: false, data: null, error: "No valid bundles for this site"};
        }

        const latestBundle = matchingBundles.sort(
            (a, b) => dayjs(b.created_at).valueOf() - dayjs(a.created_at).valueOf())[0]


        // 3. Fetch the bundle hints and SiteData for that bundle

        const bundleHintsResponse = await fetch(`/api/data/get-bundle-hints?bundle_id=${latestBundle.bundle_id}`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
        })

        const siteDataResponse = await fetch("/api/optimisation/get-latest-site-data", {
            method: "POST",
            headers: {"Content-Type": "application/json" },
            body: JSON.stringify({site_id: site_id, bundle_id: latestBundle.bundle_id})
        });

        if (!bundleHintsResponse.ok) {
            const error = `HTTP error! Status: ${bundleHintsResponse.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        if (!siteDataResponse.ok) {
            const error = `HTTP error! Status: ${siteDataResponse.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const bundleHints: BundleHint = await bundleHintsResponse.json();
        const siteData: EpochSiteData = await siteDataResponse.json();

        const siteWithHints: SiteDataWithHints = {
            siteData: siteData,
            hints: bundleHints,
        }

        return {success: true, data: siteWithHints};

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
            headers: {"Content-Type": "application/json"},
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

export const uploadMeterFile = async (file: File, site_id: string, fuelType: FuelType): Promise<ApiResponse<UploadMeterFileResponse>> => {

    try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("site_id", site_id);
        formData.append("fuel_type", fuelType);
        // formData.append("disaggregation_info", JSON.stringify(null));

        const response = await fetch("/api/data/upload-meter-file", {
            method: "POST",
            body: formData
        })

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const json: UploadMeterFileResponse = await response.json();
        return {success: true, data: json};
    } catch (error) {
        console.error("Failed to upload meter file", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
}


export const uploadPhpp = async (file: File, site_id: string): Promise<ApiResponse<PhppMetadata>> => {

    try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("site_id", site_id);

        const response = await fetch("/api/data/upload-phpp", {
            method: "POST",
            body: formData
        })

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const json: PhppMetadata = await response.json();
        return {success: true, data: json};
    } catch (error) {
        console.error("Failed to upload PHPP file", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
}


export const addSolarLocation = async (solarInfo: SolarLocation): Promise<ApiResponse<SolarLocation>> => {
    try {
        const response = await fetch("/api/data/add-solar-location", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(solarInfo)
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const location: SolarLocation = await response.json()
        return {success: true, data: location};
    } catch (error) {
        console.error("Failed to add location", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
}

export const addSiteBaseline = async(site: string, baseline: TaskData): Promise<ApiResponse<string>> => {
    const payload = {
        site_id: {site_id: site},
        baseline: baseline
    }

    try {
        const response = await fetch("/api/data/add-site-baseline", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(payload)
        })

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const baseline_id = await response.json();
        return {success: true, data: baseline_id}
    } catch (error) {
        console.error("Failed to add baseline", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
}


export const addSite = async (siteInfo: addSiteRequest): Promise<ApiResponse<addSiteRequest>> => {
    try {
        const response = await fetch("/api/data/add-site", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(siteInfo)
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const json: [addSiteRequest, string] = await response.json();
        return {success: true, data: json[0]};
    } catch (error) {
        console.error("Failed to add site", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
};


export const listCostModels = async (): Promise<ApiResponse<CostModelResponse[]>> => {

  try {
    const response = await fetch("/api/data/list-cost-models", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });

    if (!response.ok) {
      const error = `HTTP error! Status: ${response.status}`;
      console.error(error);
      return { success: false, data: null, error };
    }

    const models: CostModelResponse[] = await response.json();
    return { success: true, data: models };
  } catch (error) {
    console.error("Failed to list cost models", error);
    return { success: false, data: null, error: error instanceof Error ? error.message : String(error) };
  }
};


export const addCostModel = async (model: CostModelRequest): Promise<ApiResponse<CostModelResponse>> => {

    try {
        const response = await fetch("/api/data/add-cost-model", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(model),
        });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const created: CostModelResponse = await response.json();
        return {success: true, data: created};
    } catch (error) {
        console.error("Failed to add cost model", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
};

export const getCostModel = async (cost_model_id: string): Promise<ApiResponse<CostModelResponse>> => {

    try {
        const response = await fetch(
            `/api/data/get-cost-model?cost_model_id=${encodeURIComponent(cost_model_id)}`,
            {
                method: "POST",
                headers: {"Content-Type": "application/json"},
            });

        if (!response.ok) {
            const error = `HTTP error! Status: ${response.status}`;
            console.error(error);
            return {success: false, data: null, error};
        }

        const model: CostModelResponse = await response.json();
        return {success: true, data: model};
    } catch (error) {
        console.error("Failed to get cost model", error);
        return {success: false, data: null, error: error instanceof Error ? error.message : String(error)};
    }
};
