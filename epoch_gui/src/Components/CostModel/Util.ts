import {PiecewiseCostModel, Segment} from "./Types.ts";

export function cloneModel(m: PiecewiseCostModel): PiecewiseCostModel {
    return {
        fixed_cost: m.fixed_cost,
        final_rate: m.final_rate,
        segments: m.segments.map(s => ({...s})),
    };
}

export function sortSegments(segments: Segment[]): Segment[] {
    return [...segments].sort((a, b) => a.upper - b.upper);
}

export function normalizeNumberInput(value: string): number {
    // Gracefully coerce to number; empty or invalid -> 0
    const n = Number(value);
    return Number.isFinite(n) ? n : 0;
}

export function validateModel(model: PiecewiseCostModel): string[] {
    const errors: string[] = [];
    if (!Number.isFinite(model.fixed_cost)) errors.push("Fixed cost is not a number");
    if (!Number.isFinite(model.final_rate)) errors.push("Final rate is not a number");
    let prev = -Infinity;
    model.segments.forEach((s, idx) => {
        if (!Number.isFinite(s.upper)) errors.push(`Segment ${idx + 1}: upper is not a number`);
        if (!Number.isFinite(s.rate)) errors.push(`Segment ${idx + 1}: rate is not a number`);
        if (s.upper <= 0) errors.push(`Segment ${idx + 1}: upper should be > 0`);
        if (s.upper <= prev) errors.push(`Segment ${idx + 1}: upper must be strictly increasing`);
        prev = s.upper;
    });
    return errors;
}
