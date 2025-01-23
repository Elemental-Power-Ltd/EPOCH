

export interface SubmitSimulationRequest {
    task_data: any;

    site_data: any;
}


export type ReportDataType = { [key: string]: number[] };


export interface SimulationResult {
    objectives: any;

    report_data: ReportDataType | null;
}